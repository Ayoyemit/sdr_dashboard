from app.data.scenario_templates import all_prewarm_scenarios
from app.services.scenario_fingerprint import scenario_fingerprint

CALIBRATED_COUNTIES = ("kakamega", "kisii", "makueni", "mombasa")


def test_prewarm_templates_include_singles_and_presets():
    templates = all_prewarm_scenarios()
    names = {t.name for t in templates}
    assert "Combined strategy" in names
    assert "PPH bundle" in names
    assert "MgSO4" in names
    assert "PROMPTS" in names
    assert "Blood tracking" in names
    assert "Intrapartum sensors (AI-assisted)" in names
    assert len(templates) >= 20


def test_prewarm_dedupes_identical_templates():
    templates = all_prewarm_scenarios()
    keys: set[str] = set()
    for template in templates:
        for county in CALIBRATED_COUNTIES:
            prepared = template.model_copy(deep=True)
            prepared.county = county  # type: ignore[assignment]
            keys.add(scenario_fingerprint(prepared))
    # Some preset entries overlap (e.g. COMBINED listed twice) — deduped at schedule time.
    assert len(keys) >= 20 * len(CALIBRATED_COUNTIES)
