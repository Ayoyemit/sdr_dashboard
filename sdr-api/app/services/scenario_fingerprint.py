"""Stable fingerprint for scenario deduplication in the run cache."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.schemas.scenario import ScenarioRequest

# Display-only / UI fields — must not affect cache keys or simulation inputs.
_FINGERPRINT_IGNORE = frozenset({"name"})


def scenario_fingerprint_payload(scenario: ScenarioRequest) -> dict[str, Any]:
    payload = scenario.model_dump(mode="json")
    for key in _FINGERPRINT_IGNORE:
        payload.pop(key, None)
    return payload


def scenario_fingerprint(scenario: ScenarioRequest) -> str:
    raw = json.dumps(scenario_fingerprint_payload(scenario), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
