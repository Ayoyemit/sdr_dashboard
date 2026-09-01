import traceback
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from app.schemas.results import CompareDeltas, CompareResponse, DeltaMetric, RunResponse
from app.schemas.scenario import CompareRequest, ScenarioRequest
from app.services.cache import cache
from app.services.run_executor import submit_simulation
from app.services.run_worker import run_and_cache
from app.services.scenario_fingerprint import scenario_fingerprint

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

# Simple in-memory rate limit: IP -> list of timestamps
_rate_limit: dict[str, list[float]] = {}
RATE_LIMIT = 10
RATE_WINDOW = 60


def _check_rate_limit(request: Request) -> None:
    import time

    ip = request.client.host if request.client else "unknown"
    now = time.time()
    hits = [t for t in _rate_limit.get(ip, []) if now - t < RATE_WINDOW]
    if len(hits) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": "rate_limited",
                    "message": "Too many simulation runs. Please wait a minute and try again.",
                }
            },
        )
    hits.append(now)
    _rate_limit[ip] = hits


def _validate_county(scenario: ScenarioRequest) -> None:
    from parameter_loader import get_available_counties

    allowed = get_available_counties()
    if scenario.county not in allowed:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "county_not_supported",
                    "message": (
                        f"County '{scenario.county}' is not available. "
                        f"Supported counties: {', '.join(allowed)}."
                    ),
                }
            },
        )


def _cached_run_response(run_id: str) -> RunResponse:
    from app.schemas.results import ScenarioResult

    entry = cache.get_run(run_id)
    if entry is None or entry.status != "complete":
        raise HTTPException(status_code=404, detail={"error": {"code": "run_not_found", "message": "Run not found"}})
    data = entry.data
    return RunResponse(
        run_id=run_id,
        status="complete",
        scenario=ScenarioRequest(**data["scenario"]),
        result=ScenarioResult(**data["result"]),
        completed_at=data.get("completed_at"),
    )


@router.post("/run", response_model=RunResponse)
def run_scenario_endpoint(
    scenario: ScenarioRequest,
    request: Request,
):
    _check_rate_limit(request)
    _validate_county(scenario)

    fingerprint = scenario_fingerprint(scenario)
    cached_run_id = cache.get_run_id_by_fingerprint(fingerprint)
    if cached_run_id:
        return _cached_run_response(cached_run_id)

    pending_run_id = cache.get_pending_run_id(fingerprint)
    if pending_run_id:
        return RunResponse(
            run_id=pending_run_id,
            status="pending",
            scenario=scenario,
            estimated_seconds_remaining=90 if scenario.run.mode == "quick" else 600,
        )

    run_id = cache.new_id()
    cache.set_run(run_id, {"scenario": scenario.model_dump()}, status="pending")
    cache.mark_pending(fingerprint, run_id)
    submit_simulation(run_id, scenario, run_and_cache)
    eta = 600 if scenario.run.mode == "robust" else 90
    return RunResponse(
        run_id=run_id,
        status="pending",
        scenario=scenario,
        estimated_seconds_remaining=eta,
    )


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: str):
    entry = cache.get_run(run_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "run_not_found",
                    "message": "This result has expired or does not exist. Please re-run your scenario.",
                }
            },
        )

    data = entry.data
    scenario = ScenarioRequest(**data["scenario"])

    if entry.status == "pending":
        elapsed = max(0, int(time.time() - entry.created_at))
        base_eta = 600 if scenario.run.mode == "robust" else 90
        return RunResponse(
            run_id=run_id,
            status="pending",
            scenario=scenario,
            estimated_seconds_remaining=max(5, base_eta - elapsed),
        )
    if entry.status == "failed":
        return RunResponse(
            run_id=run_id,
            status="failed",
            scenario=scenario,
            error_message=data.get("error_message", "Simulation failed."),
        )

    from app.schemas.results import ScenarioResult

    return RunResponse(
        run_id=run_id,
        status="complete",
        scenario=scenario,
        result=ScenarioResult(**data["result"]),
        completed_at=data.get("completed_at"),
    )


def _delta(a: float, b: float) -> DeltaMetric:
    diff = b - a
    pct = (diff / abs(a) * 100) if a != 0 else None
    return DeltaMetric(a=a, b=b, diff=diff, pct=round(pct, 1) if pct is not None else None)


@router.post("/compare", response_model=CompareResponse)
def compare_scenarios(body: CompareRequest, request: Request):
    _check_rate_limit(request)
    _validate_county(body.scenario_a)
    _validate_county(body.scenario_b)

    body.scenario_a.run.mode = body.mode
    body.scenario_b.run.mode = body.mode

    comparison_id = cache.new_id()
    try:
        from app.services.runner import run_scenario

        result_a = run_scenario(body.scenario_a)
        result_b = run_scenario(body.scenario_b)
    except Exception:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "sim_error",
                    "message": "Comparison simulation failed. Please check scenario settings.",
                }
            },
        )

    sa, sb = result_a.summary, result_b.summary
    deltas = CompareDeltas(
        maternal_deaths_averted=_delta(sa.maternal_deaths_averted, sb.maternal_deaths_averted),
        severe_maternal_outcomes_averted=_delta(
            sa.severe_maternal_outcomes_averted, sb.severe_maternal_outcomes_averted
        ),
        dalys_averted=_delta(sa.dalys_averted, sb.dalys_averted),
        cost_per_daly_averted_usd=_delta(sa.cost_per_daly_averted_usd, sb.cost_per_daly_averted_usd),
        cumulative_cost_usd=_delta(sa.cumulative_cost_usd, sb.cumulative_cost_usd),
    )

    combined = (
        f"Scenario B averts {sb.maternal_deaths_averted:,.0f} maternal deaths compared with "
        f"{sa.maternal_deaths_averted:,.0f} for Scenario A "
        f"(difference: {deltas.maternal_deaths_averted.diff:+,.0f}). "
        f"Total intervention cost is ${sb.cumulative_cost_usd:,.0f} (B) vs "
        f"${sa.cumulative_cost_usd:,.0f} (A)."
    )

    response = CompareResponse(
        comparison_id=comparison_id,
        status="complete",
        scenario_a=body.scenario_a,
        scenario_b=body.scenario_b,
        result_a=result_a,
        result_b=result_b,
        deltas=deltas,
        combined_narrative=combined,
    )
    cache.set_comparison(comparison_id, response.model_dump())
    return response


@router.get("/compare/{comparison_id}", response_model=CompareResponse)
def get_comparison(comparison_id: str):
    entry = cache.get_comparison(comparison_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "run_not_found",
                    "message": "This comparison has expired or does not exist.",
                }
            },
        )
    return CompareResponse(**entry.data)
