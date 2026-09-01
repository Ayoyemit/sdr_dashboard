"""Canonical scenarios used for API prewarm (presets + singles + baseline)."""

from __future__ import annotations

from copy import deepcopy

from app.data.presets import COMBINED, HSS_INTENSIVE, MOMISH, STATUS_QUO
from app.schemas.scenario import ScenarioRequest

HSS_LIGHT = ScenarioRequest(
    name="Health system strengthening (light)",
    hss={"enabled": True, "intensity": "light"},
    treatments={"enabled": False},
    community={"enabled": False},
)

HSS_MODERATE = ScenarioRequest(
    name="Health system strengthening (moderate)",
    hss={"enabled": True, "intensity": "moderate"},
    treatments={"enabled": False},
    community={"enabled": False},
)

_SINGLE_TREATMENTS: list[tuple[str, dict]] = [
    ("PPH bundle", {"pph_bundle": True}),
    ("IV iron", {"iv_iron": True}),
    ("MgSO4", {"mgso4": True}),
    ("Antibiotics", {"antibiotics": True}),
    ("Oxytocin", {"oxytocin": True}),
    ("Ultrasound", {"ultrasound": True}),
    ("Intrapartum sensors", {"intrapartum_sensors": True}),
    (
        "Intrapartum sensors (AI-assisted)",
        {"intrapartum_sensors": True, "intrapartum_sensors_ai": True},
    ),
]

_MOMISH_SINGLES: list[tuple[str, dict]] = [
    (
        "PROMPTS",
        {
            "enabled": True,
            "prompts": {
                "enabled": True,
                "adoption": 0.6,
                "chv_engagement": 0.6,
                "intervention_fidelity": 0.75,
            },
        },
    ),
    (
        "MENTORS",
        {
            "enabled": True,
            "mentors": {
                "enabled": True,
                "adoption": 0.6,
                "attendance": 0.6,
                "fidelity": 0.75,
            },
        },
    ),
    (
        "FQA",
        {
            "enabled": True,
            "fqa": {"enabled": True, "implementation": "high", "influence_on_pulse": "low"},
        },
    ),
    (
        "PULSE",
        {"enabled": True, "pulse": {"enabled": True, "implementation": "high"}},
    ),
    (
        "Referral / EMT",
        {
            "enabled": True,
            "referral_emt": {"enabled": True, "emt_participation": 0.6},
        },
    ),
    (
        "Blood tracking",
        {
            "enabled": True,
            "blood_tracking": {"enabled": True, "level": "moderate"},
        },
    ),
]


def _single_treatment(name: str, flags: dict) -> ScenarioRequest:
    return ScenarioRequest(
        name=name,
        hss={"enabled": False, "intensity": "off"},
        treatments={"enabled": True, **flags},
        community={"enabled": False},
    )


def _momish_single(name: str, community: dict) -> ScenarioRequest:
    return ScenarioRequest(
        name=name,
        hss={"enabled": False, "intensity": "off"},
        treatments={"enabled": False},
        community=community,
    )


def all_prewarm_scenarios() -> list[ScenarioRequest]:
    """Distinct simulation configs to prewarm (county applied at prewarm time)."""
    scenarios: list[ScenarioRequest] = [
        deepcopy(STATUS_QUO),
        deepcopy(COMBINED),
        deepcopy(HSS_LIGHT),
        deepcopy(HSS_MODERATE),
        deepcopy(HSS_INTENSIVE),
        deepcopy(MOMISH),
    ]
    for label, flags in _SINGLE_TREATMENTS:
        scenarios.append(_single_treatment(label, flags))
    for label, community in _MOMISH_SINGLES:
        scenarios.append(_momish_single(label, community))

    # Deduplicate by fingerprint after county is applied in prewarm scheduler
    return scenarios
