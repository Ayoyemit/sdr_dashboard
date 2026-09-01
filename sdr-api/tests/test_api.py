import pytest
import time
from fastapi.testclient import TestClient

from app.main import app
from app.data.presets import HSS_INTENSIVE, STATUS_QUO

client = TestClient(app)


def _wait_for_run(run_id: str, timeout: float = 300) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(f"/api/v1/scenarios/{run_id}")
        assert r.status_code == 200
        data = r.json()
        if data["status"] == "complete":
            return data
        if data["status"] == "failed":
            pytest.fail(data.get("error_message", "run failed"))
        time.sleep(2)
    pytest.fail("timed out waiting for run")


def _run_and_wait(scenario) -> dict:
    r = client.post("/api/v1/scenarios/run", json=scenario.model_dump())
    assert r.status_code == 200
    data = r.json()
    if data["status"] == "pending":
        return _wait_for_run(data["run_id"])
    return data


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_presets():
    r = client.get("/api/v1/presets")
    assert r.status_code == 200
    presets = r.json()["presets"]
    assert len(presets) == 3
    recommended = [p for p in presets if p["is_recommended"]]
    assert len(recommended) == 1
    assert recommended[0]["id"] == "combined"


def test_meta_counties():
    r = client.get("/api/v1/meta/counties")
    assert r.status_code == 200
    counties = r.json()["counties"]
    ids = {c["id"] for c in counties}
    assert ids >= {"kakamega", "kisii", "makueni", "mombasa"}
    kak = [c for c in counties if c["id"] == "kakamega"][0]
    assert kak["calibrated"] is True
    assert kak["population"] > 0


@pytest.mark.slow
def test_run_kisii_quick():
    scenario = STATUS_QUO.model_copy(deep=True)
    scenario.county = "kisii"
    scenario.run.mode = "quick"
    data = _run_and_wait(scenario)
    assert data["status"] == "complete"


@pytest.mark.slow
def test_run_status_quo_quick():
    scenario = STATUS_QUO.model_copy(deep=True)
    scenario.run.mode = "quick"
    data = _run_and_wait(scenario)
    assert data["status"] == "complete"
    assert "run_id" in data
    assert data["result"]["summary"]["maternal_deaths_averted"] >= 0
    assert "indicator_series" in data["result"]["timeseries"]
    assert len(data["result"]["timeseries"]["indicator_series"]["anc_rate_per_100_lb"]["baseline"]) > 0
    assert "mortality_by_facility_level" in data["result"]["timeseries"]
    assert "facility_level_end_of_run" in data["result"]["timeseries"]


@pytest.mark.slow
def test_run_hss_intensive():
    scenario = HSS_INTENSIVE.model_copy(deep=True)
    scenario.run.mode = "quick"
    data = _run_and_wait(scenario)
    result = data["result"]
    assert result["summary"]["dalys_averted"] >= 0


@pytest.mark.slow
def test_hss_beats_status_quo():
    """HSS Intensive should avert more deaths than status quo baseline comparison."""
    sq = STATUS_QUO.model_copy(deep=True)
    sq.run.mode = "quick"
    hss = HSS_INTENSIVE.model_copy(deep=True)
    hss.run.mode = "quick"

    sq_data = _run_and_wait(sq)
    hss_data = _run_and_wait(hss)
    hss_deaths = hss_data["result"]["summary"]["maternal_deaths_averted"]
    sq_deaths = sq_data["result"]["summary"]["maternal_deaths_averted"]
    assert hss_deaths >= sq_deaths
