"""Execute a simulation run and persist results in the run cache."""

from __future__ import annotations

import traceback
from datetime import datetime, timezone

from app.schemas.scenario import ScenarioRequest
from app.services.cache import cache
from app.services.scenario_fingerprint import scenario_fingerprint


def run_and_cache(run_id: str, scenario: ScenarioRequest) -> None:
    from app.services.runner import run_scenario

    fingerprint = scenario_fingerprint(scenario)
    try:
        result = run_scenario(scenario)
        payload = {
            "scenario": scenario.model_dump(),
            "result": result.model_dump(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        cache.set_run(run_id, payload, status="complete")
        cache.link_fingerprint(fingerprint, run_id)
    except Exception as exc:
        cache.set_run(
            run_id,
            {
                "scenario": scenario.model_dump(),
                "error_message": "Simulation failed. Please check your scenario settings and try again.",
            },
            status="failed",
        )
        cache.clear_pending(fingerprint)
        print(traceback.format_exc())
        print(f"Sim error: {exc}")
