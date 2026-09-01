"""Background thread pool for CPU-heavy simulation runs."""

from __future__ import annotations

import atexit
from concurrent.futures import ThreadPoolExecutor

from app.schemas.scenario import ScenarioRequest

_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="sdr-sim")


def submit_simulation(run_id: str, scenario: ScenarioRequest, runner) -> None:
    _executor.submit(runner, run_id, scenario)


@atexit.register
def _shutdown_executor() -> None:
    _executor.shutdown(wait=False, cancel_futures=True)
