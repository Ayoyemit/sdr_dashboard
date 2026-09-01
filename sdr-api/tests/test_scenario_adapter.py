from app.adapters.scenario_to_sim import (
    _apply_community,
    _apply_treatments,
    build_applied_interventions,
)
from app.schemas.scenario import ScenarioRequest


def _base_scenario() -> ScenarioRequest:
    return ScenarioRequest(name="Test", county="kakamega")


def _empty_sim_dicts():
    return {}, {}, {}


def test_intrapartum_sensors_standard():
    scenario = _base_scenario()
    scenario.treatments.intrapartum_sensors = True
    scenario.treatments.intrapartum_sensors_ai = False

    i_flags, i_s, i_e = _empty_sim_dicts()
    _apply_treatments(scenario, i_flags, i_s, i_e)

    assert i_flags["flag_intrasensor"] == 1
    assert i_flags.get("flag_sensor_ai", 0) == 0
    applied = build_applied_interventions(scenario)
    assert any(i["name"] == "Intrapartum sensors" and i["intensity"] == "Standard" for i in applied)


def test_intrapartum_sensors_ai():
    scenario = _base_scenario()
    scenario.treatments.intrapartum_sensors = True
    scenario.treatments.intrapartum_sensors_ai = True

    i_flags, i_s, i_e = _empty_sim_dicts()
    _apply_treatments(scenario, i_flags, i_s, i_e)

    assert i_flags["flag_intrasensor"] == 1
    assert i_flags["flag_sensor_ai"] == 1
    assert i_e["sens_sensor"] == 0.95
    assert i_e["spec_sensor"] == 0.95
    applied = build_applied_interventions(scenario)
    assert any(i["name"] == "Intrapartum sensors" and i["intensity"] == "AI-assisted" for i in applied)


def test_blood_tracking_without_community_enabled():
    scenario = _base_scenario()
    scenario.community.enabled = False
    scenario.community.blood_tracking.enabled = True
    scenario.community.blood_tracking.level = "moderate"

    i_flags, i_hss = {}, {}
    _apply_community(scenario, i_flags, i_hss)

    assert i_flags["flag_blood"] == 1
    assert i_flags["flag_blood_tracking"] == 1
    assert i_hss["blood_adoption"] == 0.5
    applied = build_applied_interventions(scenario)
    assert any(i["name"] == "Blood tracking" and i["intensity"] == "Moderate" for i in applied)
