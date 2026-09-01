from app.data.presets import STATUS_QUO
from app.services.cache import cache
from app.services.scenario_fingerprint import scenario_fingerprint


def test_scenario_fingerprint_stable():
    a = STATUS_QUO.model_copy(deep=True)
    b = STATUS_QUO.model_copy(deep=True)
    assert scenario_fingerprint(a) == scenario_fingerprint(b)


def test_fingerprint_ignores_display_name():
    a = STATUS_QUO.model_copy(deep=True)
    b = STATUS_QUO.model_copy(deep=True)
    b.name = "Renamed for reporting only"
    assert scenario_fingerprint(a) == scenario_fingerprint(b)


def test_fingerprint_links_to_cached_run():
    scenario = STATUS_QUO.model_copy(deep=True)
    fingerprint = scenario_fingerprint(scenario)
    run_id = cache.new_id()
    cache.set_run(run_id, {"scenario": scenario.model_dump(), "result": {}}, status="complete")
    cache.link_fingerprint(fingerprint, run_id)
    assert cache.get_run_id_by_fingerprint(fingerprint) == run_id
