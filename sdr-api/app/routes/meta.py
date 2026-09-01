from fastapi import APIRouter

from app.data.presets import get_presets_response

router = APIRouter(prefix="/api/v1", tags=["meta"])


def _load_counties_meta() -> list[dict]:
    from parameter_loader import get_counties_catalog

    return get_counties_catalog()


@router.get("/meta/counties")
def meta_counties():
    return {"counties": _load_counties_meta()}


@router.get("/meta/parameters")
def meta_parameters():
    return {
        "intensity_ranges": {
            "hss": {
                "off": {"label": "Off", "range": [0, 0], "description": "Baseline / no HSS intervention"},
                "light": {"label": "Light", "range": [60, 69], "description": "Modest demand-side investment"},
                "moderate": {"label": "Moderate", "range": [70, 79], "description": "Stronger demand + matching supply"},
                "intensive": {"label": "Intensive", "range": [80, 95], "description": "Aggressive demand + matched supply"},
            },
            "fqa": {"low": {"label": "Low"}, "high": {"label": "High"}},
            "pulse": {"low": {"label": "Low"}, "high": {"label": "High"}},
        },
        "timeline_constraints": {
            "min_total_years": 1,
            "max_total_years": 10,
            "default_implementation_years": 3,
            "default_maintenance_years": 1,
        },
    }


@router.get("/presets")
def list_presets():
    return get_presets_response()
