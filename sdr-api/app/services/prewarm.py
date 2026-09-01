"""Prewarm preset and single-intervention scenarios for all calibrated counties."""

from __future__ import annotations

import os

from app.data.scenario_templates import all_prewarm_scenarios
from app.schemas.scenario import ScenarioRequest
from app.services.cache import cache
from app.services.run_executor import submit_simulation
from app.services.run_worker import run_and_cache
from app.services.scenario_fingerprint import scenario_fingerprint

CALIBRATED_COUNTIES = ("kakamega", "kisii", "makueni", "mombasa")


def _schedule_one(scenario: ScenarioRequest, county: str) -> None:
    prepared = scenario.model_copy(deep=True)
    prepared.county = county  # type: ignore[assignment]
    fingerprint = scenario_fingerprint(prepared)
    if cache.get_run_id_by_fingerprint(fingerprint):
        return
    if cache.get_pending_run_id(fingerprint):
        return
    run_id = cache.new_id()
    cache.set_run(run_id, {"scenario": prepared.model_dump()}, status="pending")
    cache.mark_pending(fingerprint, run_id)
    submit_simulation(run_id, prepared, run_and_cache)


def schedule_prewarm() -> None:
    if os.environ.get("DISABLE_PREWARM", "").lower() in {"1", "true", "yes"}:
        return

    seen: set[str] = set()
    for template in all_prewarm_scenarios():
        for county in CALIBRATED_COUNTIES:
            prepared = template.model_copy(deep=True)
            prepared.county = county  # type: ignore[assignment]
            fingerprint = scenario_fingerprint(prepared)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            _schedule_one(template, county)
