"""Translate clean API ScenarioRequest into sim i_flags / i_HSS / i_E / i_S dicts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np

from app.data.hss_presets import CAPACITY_MATCH, DEMAND_SCENARIOS
from app.schemas.scenario import ScenarioRequest

# Imported after sim path is configured in runner
_get_slider_params = None
_reset_flags = None
_reset_E = None
_reset_HSS = None
_reset_S = None
_get_P_l45 = None
_get_parameters = None
_calculate_derived_parameters = None
_get_fqa_pulse_modifier_options = None

FQA_FIDELITY_OVERRIDE = {"Moderate": 0.5, "High": 0.95}
PULSE_FIDELITY_OVERRIDE = {"Moderate": 0.5, "High": 0.95}
BLOOD_TRACKING_LEVEL = {"current": 0.25, "moderate": 0.5, "intensive": 0.95}


def _ensure_sim_imports():
    global _get_slider_params, _reset_flags, _reset_E, _reset_HSS, _reset_S, _get_P_l45
    global _get_parameters, _calculate_derived_parameters, _get_fqa_pulse_modifier_options
    if _reset_flags is None:
        from global_func import get_P_l45, reset_E, reset_flags, reset_HSS, reset_S
        from parameter_loader import (
            calculate_derived_parameters,
            get_fqa_pulse_modifier_options,
            get_parameters,
            get_slider_params,
        )

        _get_slider_params = get_slider_params
        _reset_flags = reset_flags
        _reset_E = reset_E
        _reset_HSS = reset_HSS
        _reset_S = reset_S
        _get_P_l45 = get_P_l45
        _get_parameters = get_parameters
        _calculate_derived_parameters = calculate_derived_parameters
        _get_fqa_pulse_modifier_options = get_fqa_pulse_modifier_options


def _fidelity_key(implementation: str) -> str:
    return "High" if implementation == "high" else "Moderate"


def _modifier_level(influence: str) -> str:
    return "High" if influence == "high" else "Low"


def _get_fqa_implementation_index(fidelity_choice: str, county: str) -> float:
    if fidelity_choice in FQA_FIDELITY_OVERRIDE:
        return FQA_FIDELITY_OVERRIDE[fidelity_choice]
    try:
        param = _get_parameters(rng=np.random.default_rng(0), county=county)
        param = _calculate_derived_parameters(param)
        return float(np.clip(param.get("fqa_implementation_index", 0.0), 0.0, 1.0))
    except Exception:
        return 0.0


def _get_pulse_implementation_index(fidelity_choice: str, county: str) -> float:
    if fidelity_choice in PULSE_FIDELITY_OVERRIDE:
        return PULSE_FIDELITY_OVERRIDE[fidelity_choice]
    try:
        param = _get_parameters(rng=np.random.default_rng(0), county=county)
        param = _calculate_derived_parameters(param)
        return float(np.clip(param.get("pulse_implementation_index", 0.0), 0.0, 1.0))
    except Exception:
        return 0.0


def _apply_hss(req: ScenarioRequest, i_flags: dict, i_hss: dict, slider_params: dict) -> list[str]:
    warnings: list[str] = []
    hss = req.hss
    if not hss.enabled or hss.intensity == "off":
        return warnings

    preset = DEMAND_SCENARIOS.get(hss.intensity)
    if preset is None:
        return warnings

    scenario_key = preset["key"]
    i_flags["flag_SDR"] = 1
    i_flags["flag_CHV"] = 1
    i_flags["flag_ANC"] = 1
    i_flags["flag_LB"] = 1
    i_flags["flag_performance"] = 1
    i_flags["flag_capacity"] = 1
    i_flags["flag_labor"] = 1
    i_flags["flag_equipment"] = 1

    p_anc = hss.p_anc if hss.p_anc is not None else preset["P_ANC"] / 100.0
    p_l45_raw = preset["P_L45"]
    p_l45_exp = _get_P_l45(p_anc, slider_params)
    min_l45 = round(p_l45_exp * 100) if p_l45_exp is not None else 0
    p_l45 = hss.p_l45 if hss.p_l45 is not None else max(min_l45, p_l45_raw) / 100.0

    i_hss["P_ANC"] = p_anc
    i_hss["P_L45"] = p_l45
    i_hss["CHV_memory"] = hss.chv_memory or "Logistic Decay"
    i_hss["tau_decay"] = 6
    i_hss["knowledge"] = 1.0
    i_hss["capacity_added"] = (
        hss.capacity_added if hss.capacity_added is not None else CAPACITY_MATCH[scenario_key] / 100.0
    )
    i_hss["labor_ratio"] = 1.0
    i_hss["sensor_ratio"] = 1.0

    refer_on = hss.refer_enabled if hss.refer_enabled is not None else True
    transfer_on = hss.transfer_enabled if hss.transfer_enabled is not None else True
    if refer_on:
        i_flags["flag_refer"] = 1
        i_hss["P_refer"] = 1.0
    if transfer_on:
        i_flags["flag_transfer"] = 1
        i_hss["P_transfer"] = 1.0

    return warnings


def _apply_treatments(req: ScenarioRequest, i_flags: dict, i_s: dict, i_e: dict) -> None:
    t = req.treatments
    if not t.enabled and not t.intrapartum_sensors:
        return
    mapping = [
        ("pph_bundle", "flag_pph_bundle", "pph_bundle"),
        ("iv_iron", "flag_iv_iron", "iv_iron"),
        ("mgso4", "flag_MgSO4", "MgSO4"),
        ("antibiotics", "flag_antibiotics", "antibiotics"),
        ("oxytocin", "flag_oxytocin", "oxytocin"),
    ]
    for attr, flag_key, s_key in mapping:
        if getattr(t, attr):
            i_flags[flag_key] = 1
            i_s[s_key] = 1.0
    if t.ultrasound:
        i_flags["flag_us"] = 1
        i_s["US"] = 1.0
    if t.intrapartum_sensors:
        i_flags["flag_intrasensor"] = 1
        if t.intrapartum_sensors_ai:
            i_flags["flag_sensor_ai"] = 1
            i_e["sens_sensor"] = 0.95
            i_e["spec_sensor"] = 0.95
        else:
            i_flags["flag_sensor_ai"] = 0


def _apply_community(req: ScenarioRequest, i_flags: dict, i_hss: dict) -> list[str]:
    warnings: list[str] = []
    c = req.community
    county = req.county or "kakamega"
    if not c.enabled and not c.blood_tracking.enabled:
        return warnings

    if c.enabled:
        if c.prompts.enabled:
            i_flags["flag_PROMPTS"] = 1
            if c.prompts.adoption is not None:
                i_hss["adoption_prompts"] = c.prompts.adoption
            if c.prompts.chv_engagement is not None:
                i_hss["chv_engagement"] = c.prompts.chv_engagement
            if c.prompts.intervention_fidelity is not None:
                i_hss["intervention_fidelity"] = c.prompts.intervention_fidelity
                i_hss["prompts_effect"] = c.prompts.intervention_fidelity

        if c.mentors.enabled:
            i_flags["flag_MENTOR"] = 1
            if c.mentors.adoption is not None:
                i_hss["mentor_adoption"] = c.mentors.adoption
            if c.mentors.attendance is not None:
                i_hss["mentor_attendance"] = c.mentors.attendance
            if c.mentors.fidelity is not None:
                i_hss["mentor_fidelity"] = c.mentors.fidelity

        if c.pulse.enabled:
            i_flags["flag_pulse"] = 1
            pulse_key = _fidelity_key(c.pulse.implementation)
            pulse_index = _get_pulse_implementation_index(pulse_key, county)
            i_hss["pulse_implementation_index"] = pulse_index
        else:
            i_hss["pulse_implementation_index"] = 0.0

        if c.fqa.enabled:
            i_flags["flag_fqa"] = 1
            fqa_key = _fidelity_key(c.fqa.implementation)
            fqa_index = _get_fqa_implementation_index(fqa_key, county)
            i_hss["fqa_implementation_index"] = fqa_index
        else:
            i_hss["fqa_implementation_index"] = 0.0

        if c.fqa.enabled or c.pulse.enabled:
            modifier_options = _get_fqa_pulse_modifier_options()
            modifier_level = _modifier_level(c.fqa.influence_on_pulse)
            i_hss["fqa_pulse_modifier_level"] = modifier_level
            i_hss["fqa_pulse_modifier"] = modifier_options[modifier_level]

        if c.referral_emt.enabled:
            i_flags["flag_emt"] = 1
            participation = c.referral_emt.emt_participation if c.referral_emt.emt_participation is not None else 1.0
            i_hss["emt_participation"] = participation
            i_hss["emt_intensity"] = participation
        else:
            i_hss["emt_intensity"] = 0.0

    if c.blood_tracking.enabled:
        i_flags["flag_blood"] = 1
        i_flags["flag_blood_tracking"] = 1
        i_hss["blood_adoption"] = BLOOD_TRACKING_LEVEL.get(c.blood_tracking.level, 0.25)
    else:
        i_hss["blood_adoption"] = 0.0

    return warnings


def sync_param_momish_from_hss(i_param: dict, i_hss: dict) -> None:
    i_param["intervention_fidelity"] = float(
        i_hss.get("prompts_effect", i_param.get("intervention_fidelity", 0.87))
    )
    if i_hss.get("OR_anc4p") is not None:
        i_param["OR_anc4p"] = float(i_hss["OR_anc4p"])
    for key in ("mentor_adoption", "mentor_attendance", "mentor_fidelity"):
        if key in i_hss:
            i_param[key] = float(i_hss[key])
    if i_hss.get("fqa_pulse_modifier") is not None:
        i_param["fqa_pulse_modifier_level"] = i_hss.get("fqa_pulse_modifier_level", "Medium")
        i_param["fqa_pulse_modifier"] = float(i_hss["fqa_pulse_modifier"])
    if i_hss.get("pulse_implementation_index") is not None:
        i_param["pulse_implementation_index"] = float(i_hss["pulse_implementation_index"])
    if i_hss.get("fqa_implementation_index") is not None:
        i_param["fqa_implementation_index"] = float(i_hss["fqa_implementation_index"])
    if i_hss.get("emt_participation") is not None:
        i_param["emt_participation"] = float(i_hss["emt_participation"])
    if i_hss.get("emt_intensity") is not None:
        i_param["emt_intensity"] = float(i_hss["emt_intensity"])


def scenario_to_sim_inputs(req: ScenarioRequest) -> tuple[dict, dict, dict, dict, list[str]]:
    """Return (i_flags, i_E, i_S, i_HSS, warnings)."""
    _ensure_sim_imports()
    county = req.county or "kakamega"
    slider_params = _get_slider_params(county=county)

    i_flags = _reset_flags()
    i_e = _reset_E()
    i_hss = _reset_HSS(slider_params)
    i_s = deepcopy(_reset_S(slider_params))

    warnings: list[str] = []
    warnings.extend(_apply_hss(req, i_flags, i_hss, slider_params))
    _apply_treatments(req, i_flags, i_s, i_e)
    warnings.extend(_apply_community(req, i_flags, i_hss))

    return i_flags, i_e, i_s, i_hss, warnings


def build_applied_interventions(req: ScenarioRequest) -> list[dict[str, Any]]:
    from app.data.hss_presets import INTENSITY_LABELS

    items: list[dict[str, Any]] = []
    if req.hss.enabled and req.hss.intensity != "off":
        items.append(
            {
                "pillar": "hss",
                "name": "Health system strengthening",
                "intensity": INTENSITY_LABELS.get(req.hss.intensity),
                "is_wired_in_model": True,
            }
        )
    if req.treatments.enabled:
        for label, attr in [
            ("PPH bundle", "pph_bundle"),
            ("IV iron", "iv_iron"),
            ("MgSO4", "mgso4"),
            ("Antibiotics", "antibiotics"),
            ("Oxytocin", "oxytocin"),
            ("Ultrasound", "ultrasound"),
        ]:
            if getattr(req.treatments, attr):
                items.append(
                    {"pillar": "treatments", "name": label, "is_wired_in_model": True}
                )
    if req.treatments.intrapartum_sensors:
        items.append(
            {
                "pillar": "treatments",
                "name": "Intrapartum sensors",
                "intensity": "AI-assisted" if req.treatments.intrapartum_sensors_ai else "Standard",
                "is_wired_in_model": True,
            }
        )
    if req.community.enabled:
        if req.community.prompts.enabled:
            items.append(
                {"pillar": "community", "name": "PROMPTS", "is_wired_in_model": True}
            )
        if req.community.mentors.enabled:
            items.append(
                {"pillar": "community", "name": "MENTORS", "is_wired_in_model": True}
            )
        if req.community.fqa.enabled:
            items.append(
                {"pillar": "community", "name": "FQA", "is_wired_in_model": True}
            )
        if req.community.pulse.enabled:
            items.append(
                {"pillar": "community", "name": "PULSE", "is_wired_in_model": True}
            )
        if req.community.referral_emt.enabled:
            items.append(
                {"pillar": "community", "name": "Referral / EMT", "is_wired_in_model": True}
            )
    if req.community.blood_tracking.enabled:
        items.append(
            {
                "pillar": "community",
                "name": "Blood tracking",
                "intensity": req.community.blood_tracking.level.title(),
                "is_wired_in_model": True,
            }
        )
    return items
