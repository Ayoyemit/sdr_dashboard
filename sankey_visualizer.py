"""
Sankey Diagram Visualization Module for Maternal Health Pathways
Extracted from all_pathway_sankey.ipynb for integration with Streamlit dashboard
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.colors import qualitative
from pandas.api.types import CategoricalDtype
import warnings
from typing import Dict, List, Optional, Any
warnings.filterwarnings('ignore')

SHARE_THRESHOLD = 3.0  # percentage points
COUNT_THRESHOLD = 25   # absolute cases


def _column_or_zeros(df: pd.DataFrame, column: str) -> np.ndarray:
    if column in df.columns:
        return df[column].to_numpy()
    return np.zeros(len(df), dtype=float)


def _format_share_change(
    label: str,
    baseline_series: pd.Series,
    scenario_series: pd.Series,
    baseline_total_mothers: int,
    scenario_total_mothers: int,
    force: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Format share change with percentages relative to total starting mothers.
    Returns a detailed insight string showing baseline %, scenario %, and difference.
    """
    if baseline_series is None or scenario_series is None:
        return None

    baseline_clean = pd.Series(baseline_series).dropna()
    scenario_clean = pd.Series(scenario_series).dropna()

    if baseline_clean.empty and scenario_clean.empty:
        return None

    baseline_numeric = baseline_clean.astype(float)
    scenario_numeric = scenario_clean.astype(float)

    baseline_count = int(baseline_numeric.sum())
    scenario_count = int(scenario_numeric.sum())

    # Calculate percentages relative to total starting mothers
    baseline_pct_of_total = (baseline_count / baseline_total_mothers * 100) if baseline_total_mothers > 0 else float("nan")
    scenario_pct_of_total = (scenario_count / scenario_total_mothers * 100) if scenario_total_mothers > 0 else float("nan")

    if pd.isna(baseline_pct_of_total) or pd.isna(scenario_pct_of_total):
        return None

    delta_pts = scenario_pct_of_total - baseline_pct_of_total
    if abs(delta_pts) < 0.1 and not force:
        return None

    # Calculate relative change
    if baseline_count > 0:
        delta_rel = ((scenario_count - baseline_count) / baseline_count) * 100
    else:
        delta_rel = float("nan")

    # Format the insight text
    if abs(delta_pts) < 0.1 and baseline_count == scenario_count:
        text = (
            f"{label}: {baseline_count:,} mothers ({baseline_pct_of_total:.1f}% of total) "
            f"in both baseline and scenario. No change."
        )
    else:
        direction = "increased" if delta_pts > 0 else "decreased"
        sign = "+" if delta_pts > 0 else "−"
        
        text = (
            f"{label}: {baseline_count:,} mothers ({baseline_pct_of_total:.1f}% of total) at baseline → "
            f"{scenario_count:,} mothers ({scenario_pct_of_total:.1f}% of total) in scenario. "
            f"Change: {sign}{abs(delta_pts):.1f} percentage points"
        )
        
        if not pd.isna(delta_rel):
            text += f" ({sign}{abs(delta_rel):.1f}% relative change)"
        text += "."

    return {
        "text": text,
        "magnitude": abs(delta_pts),
        "type": "share",
        "delta": delta_pts,
        "baseline_pct": baseline_pct_of_total,
        "scenario_pct": scenario_pct_of_total,
        "baseline_count": baseline_count,
        "scenario_count": scenario_count,
    }


def _format_count_change(
    label: str, 
    baseline: int, 
    scenario: int, 
    baseline_total_mothers: int,
    scenario_total_mothers: int,
    force: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Format count change with percentages relative to total starting mothers.
    Returns a detailed insight string showing baseline %, scenario %, and difference.
    """
    if baseline == 0 and scenario == 0 and not force:
        return None
    delta = scenario - baseline
    if delta == 0 and not force:
        return None
    
    # Calculate percentages relative to total starting mothers
    baseline_pct_of_total = (baseline / baseline_total_mothers * 100) if baseline_total_mothers > 0 else float("nan")
    scenario_pct_of_total = (scenario / scenario_total_mothers * 100) if scenario_total_mothers > 0 else float("nan")
    
    if delta == 0 and force:
        text = (
            f"{label}: {baseline:,} cases ({baseline_pct_of_total:.1f}% of total) "
            f"in both baseline and scenario. No change."
        )
    else:
        direction = "increased" if delta > 0 else "decreased"
        sign = "+" if delta > 0 else "−"
        
        if baseline > 0:
            pct_change = (delta / baseline) * 100
            pct_text = f"{sign}{abs(pct_change):.1f}% relative change"
        else:
            pct_text = "new impact" if delta > 0 else "complete removal"
        
        text = (
            f"{label}: {baseline:,} cases ({baseline_pct_of_total:.1f}% of total) at baseline → "
            f"{scenario:,} cases ({scenario_pct_of_total:.1f}% of total) in scenario. "
            f"Change: {sign}{abs(delta):,} cases ({sign}{abs(scenario_pct_of_total - baseline_pct_of_total):.1f} percentage points, {pct_text})."
        )
    
    return {
        "text": text,
        "magnitude": abs(delta),
        "type": "count",
        "delta": delta,
        "baseline_pct": baseline_pct_of_total,
        "scenario_pct": scenario_pct_of_total,
        "baseline_count": baseline,
        "scenario_count": scenario,
    }


def _passes_threshold(metric: Dict[str, Any]) -> bool:
    if metric is None:
        return False
    if metric["type"] == "share":
        return metric["magnitude"] >= SHARE_THRESHOLD
    if metric["type"] == "count":
        return metric["magnitude"] >= COUNT_THRESHOLD
    return False


def _build_summary(final_metric: Optional[Dict[str, Any]], metrics: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    if final_metric:
        bullets = [
            metric["text"]
            for metric in metrics
            if _passes_threshold(metric) and metric["text"] != final_metric["text"]
        ]
        return {"headline": final_metric["text"], "bullets": bullets}

    if not metrics:
        return {"headline": "No material pathway changes detected between baseline and scenario.", "bullets": []}

    sorted_metrics = sorted(metrics, key=lambda item: item["magnitude"], reverse=True)
    headline_metric = sorted_metrics[0]
    bullets = [metric["text"] for metric in sorted_metrics[1:] if _passes_threshold(metric)]
    return {"headline": headline_metric["text"], "bullets": bullets}


def _anc_complication_subset(df: pd.DataFrame) -> pd.DataFrame:
    complication_labels = np.full(len(df), None, dtype=object)
    complication_labels[_column_or_zeros(df, "i_pph") == 1] = "PPH"
    complication_labels[_column_or_zeros(df, "i_OL") == 1] = "Obstructed Labor"
    complication_labels[_column_or_zeros(df, "i_PL") == 1] = "Prolonged Labor"
    complication_labels[_column_or_zeros(df, "i_eclampsia") == 1] = "Eclampsia"
    complication_labels[_column_or_zeros(df, "i_mat_sepsis") == 1] = "Sepsis"
    complication_labels[_column_or_zeros(df, "i_hypoxia") == 1] = "Hypoxia"

    valid_mask = pd.notna(complication_labels)
    subset = df.loc[valid_mask].copy()
    subset["_complication_stage"] = complication_labels[valid_mask]
    return subset


def _intrapartum_subset(df: pd.DataFrame) -> pd.DataFrame:
    if "i_mod" not in df.columns:
        return df
    return df[df["i_mod"].notna()]


def _summarize_risk_delivery(baseline: pd.DataFrame, scenario: pd.DataFrame) -> Dict[str, List[str]]:
    metrics: List[Dict[str, Any]] = []
    baseline_total = len(baseline)
    scenario_total = len(scenario)
    final_metric: Optional[Dict[str, Any]] = None

    # Delivery location insights - show specific locations
    if all(col in baseline.columns for col in ["i_loc"]) and all(col in scenario.columns for col in ["i_loc"]):
        # L4 deliveries (key metric as per user example)
        l4_metric = _format_share_change(
            "Deliveries at L4",
            baseline["i_loc"] == 2,
            scenario["i_loc"] == 2,
            baseline_total,
            scenario_total,
            force=True,
        )
        if l4_metric:
            final_metric = l4_metric

        # L5 deliveries
        l5_metric = _format_share_change(
            "Deliveries at L5",
            baseline["i_loc"] == 3,
            scenario["i_loc"] == 3,
            baseline_total,
            scenario_total,
        )
        if l5_metric:
            metrics.append(l5_metric)

        # L2/L3 deliveries
        l2l3_metric = _format_share_change(
            "Deliveries at L2/L3",
            baseline["i_loc"] == 1,
            scenario["i_loc"] == 1,
            baseline_total,
            scenario_total,
        )
        if l2l3_metric:
            metrics.append(l2l3_metric)

        # Home deliveries
        home_metric = _format_share_change(
            "Deliveries at home",
            baseline["i_loc"] == 0,
            scenario["i_loc"] == 0,
            baseline_total,
            scenario_total,
        )
        if home_metric:
            metrics.append(home_metric)

    # POCUS coverage (first stage in pathway)
    if all(col in baseline.columns for col in ["i_pocus"]) and all(col in scenario.columns for col in ["i_pocus"]):
        pocus_metric = _format_share_change(
            "POCUS coverage",
            baseline["i_pocus"],
            scenario["i_pocus"],
            baseline_total,
            scenario_total,
        )
        if pocus_metric:
            metrics.append(pocus_metric)

    # Risk stratification insights
    if all(col in baseline.columns for col in ["i_risk"]) and all(col in scenario.columns for col in ["i_risk"]):
        # High-risk mothers
        risk_metric = _format_share_change(
            "High-risk mothers identified",
            baseline["i_risk"],
            scenario["i_risk"],
            baseline_total,
            scenario_total,
        )
        if risk_metric:
            metrics.append(risk_metric)

        # Low-risk mothers
        low_risk_metric = _format_share_change(
            "Low-risk mothers identified",
            baseline["i_risk"] == 0,
            scenario["i_risk"] == 0,
            baseline_total,
            scenario_total,
        )
        if low_risk_metric:
            metrics.append(low_risk_metric)

    # Risk prediction insights
    if all(col in baseline.columns for col in ["i_risk_pred"]) and all(col in scenario.columns for col in ["i_risk_pred"]):
        # High-risk predictions
        risk_pred_metric = _format_share_change(
            "High-risk predictions",
            baseline["i_risk_pred"],
            scenario["i_risk_pred"],
            baseline_total,
            scenario_total,
        )
        if risk_pred_metric:
            metrics.append(risk_pred_metric)

        # Low-risk predictions
        low_risk_pred_metric = _format_share_change(
            "Low-risk predictions",
            baseline["i_risk_pred"] == 0,
            scenario["i_risk_pred"] == 0,
            baseline_total,
            scenario_total,
        )
        if low_risk_pred_metric:
            metrics.append(low_risk_pred_metric)

    return _build_summary(final_metric, metrics)


def _summarize_anc_pathway(baseline: pd.DataFrame, scenario: pd.DataFrame) -> Dict[str, List[str]]:
    metrics: List[Dict[str, Any]] = []
    baseline_subset = _anc_complication_subset(baseline)
    scenario_subset = _anc_complication_subset(scenario)
    baseline_total = len(baseline)
    scenario_total = len(scenario)

    final_metric: Optional[Dict[str, Any]] = None
    if "i_mat_death" in baseline.columns and "i_mat_death" in scenario.columns:
        final_metric = _format_count_change(
            "Maternal deaths in complication cases",
            int(baseline_subset["i_mat_death"].sum()) if not baseline_subset.empty else 0,
            int(scenario_subset["i_mat_death"].sum()) if not scenario_subset.empty else 0,
            baseline_total,
            scenario_total,
            force=True,
        )

    # ANC coverage for all mothers (not just complication cases)
    if all(col in baseline.columns for col in ["i_ANC"]) and all(col in scenario.columns for col in ["i_ANC"]):
        anc_all_metric = _format_share_change(
            "ANC coverage (all mothers)",
            baseline["i_ANC"],
            scenario["i_ANC"],
            baseline_total,
            scenario_total,
        )
        if anc_all_metric:
            metrics.append(anc_all_metric)

    # Complication cases overall
    baseline_complication_count = len(baseline_subset) if not baseline_subset.empty else 0
    scenario_complication_count = len(scenario_subset) if not scenario_subset.empty else 0
    if baseline_complication_count > 0 or scenario_complication_count > 0:
        complication_metric = _format_count_change(
            "Mothers with complications",
            baseline_complication_count,
            scenario_complication_count,
            baseline_total,
            scenario_total,
        )
        if complication_metric:
            metrics.append(complication_metric)

    # Specific complication types
    complication_types = {
        "i_pph": "PPH (Postpartum Hemorrhage) cases",
        "i_OL": "Obstructed Labor cases",
        "i_PL": "Prolonged Labor cases",
        "i_eclampsia": "Eclampsia cases",
        "i_mat_sepsis": "Maternal Sepsis cases",
        "i_hypoxia": "Hypoxia cases",
    }
    
    for col, label in complication_types.items():
        if col in baseline.columns and col in scenario.columns and not baseline_subset.empty and not scenario_subset.empty:
            comp_metric = _format_share_change(
                label,
                baseline_subset[col] == 1 if col in baseline_subset.columns else None,
                scenario_subset[col] == 1 if col in scenario_subset.columns else None,
                baseline_total,
                scenario_total,
            )
            if comp_metric:
                metrics.append(comp_metric)

    # Anemia among complication cases
    if (
        all(col in baseline.columns for col in ["i_anemia"])
        and all(col in scenario.columns for col in ["i_anemia"])
        and not baseline_subset.empty
        and not scenario_subset.empty
    ):
        anemia_metric = _format_share_change(
            "Anemia (among complication cases)",
            baseline_subset["i_anemia"],
            scenario_subset["i_anemia"],
            baseline_total,
            scenario_total,
        )
        if anemia_metric:
            metrics.append(anemia_metric)

    return _build_summary(final_metric, metrics)


def _summarize_intrapartum(baseline: pd.DataFrame, scenario: pd.DataFrame) -> Dict[str, List[str]]:
    metrics: List[Dict[str, Any]] = []
    baseline_subset = _intrapartum_subset(baseline)
    scenario_subset = _intrapartum_subset(scenario)
    baseline_total = len(baseline)
    scenario_total = len(scenario)

    final_metric: Optional[Dict[str, Any]] = None
    if (
        "i_unnecessary_cs" in baseline.columns
        and "i_unnecessary_cs" in scenario.columns
        and not baseline_subset.empty
        and not scenario_subset.empty
    ):
        final_metric = _format_share_change(
            "Unnecessary cesarean deliveries",
            baseline_subset["i_unnecessary_cs"],
            scenario_subset["i_unnecessary_cs"],
            baseline_total,
            scenario_total,
            force=True,
        )

    # Delivery location insights - specific locations
    if (
        "i_loc" in baseline.columns
        and "i_loc" in scenario.columns
        and not baseline_subset.empty
        and not scenario_subset.empty
    ):
        # L4 deliveries
        l4_metric = _format_share_change(
            "Deliveries at L4",
            baseline_subset["i_loc"] == 2,
            scenario_subset["i_loc"] == 2,
            baseline_total,
            scenario_total,
        )
        if l4_metric:
            metrics.append(l4_metric)

        # L5 deliveries
        l5_metric = _format_share_change(
            "Deliveries at L5",
            baseline_subset["i_loc"] == 3,
            scenario_subset["i_loc"] == 3,
            baseline_total,
            scenario_total,
        )
        if l5_metric:
            metrics.append(l5_metric)

        # L2/L3 deliveries
        l2l3_metric = _format_share_change(
            "Deliveries at L2/L3",
            baseline_subset["i_loc"] == 1,
            scenario_subset["i_loc"] == 1,
            baseline_total,
            scenario_total,
        )
        if l2l3_metric:
            metrics.append(l2l3_metric)

        # Home deliveries
        home_metric = _format_share_change(
            "Deliveries at home",
            baseline_subset["i_loc"] == 0,
            scenario_subset["i_loc"] == 0,
            baseline_total,
            scenario_total,
        )
        if home_metric:
            metrics.append(home_metric)

    # Sensor monitoring
    if (
        "i_sensors" in baseline.columns
        and "i_sensors" in scenario.columns
        and not baseline_subset.empty
        and not scenario_subset.empty
    ):
        sensors_metric = _format_share_change(
            "Labor monitoring with sensors",
            baseline_subset["i_sensors"],
            scenario_subset["i_sensors"],
            baseline_total,
            scenario_total,
        )
        if sensors_metric:
            metrics.append(sensors_metric)

    # Delivery mode insights - all modes
    if (
        "i_mod" in baseline.columns
        and "i_mod" in scenario.columns
        and not baseline_subset.empty
        and not scenario_subset.empty
    ):
        for mode_label, display_name in {
            "SVD": "Spontaneous vaginal deliveries",
            "AVD": "Assisted vaginal deliveries",
            "EmCS": "Emergency cesareans",
            "ELCS": "Elective cesareans",
        }.items():
            mode_metric = _format_share_change(
                display_name,
                baseline_subset["i_mod"] == mode_label,
                scenario_subset["i_mod"] == mode_label,
                baseline_total,
                scenario_total,
            )
            if mode_metric:
                metrics.append(mode_metric)

    # Actual complications during intrapartum
    if not baseline_subset.empty and not scenario_subset.empty:
        complication_types = {
            "i_PL": "Prolonged Labor cases",
            "i_OL": "Obstructed Labor cases",
            "i_hypoxia": "Hypoxia cases",
        }
        
        for col, label in complication_types.items():
            if col in baseline_subset.columns and col in scenario_subset.columns:
                comp_metric = _format_share_change(
                    label,
                    baseline_subset[col] == 1,
                    scenario_subset[col] == 1,
                    baseline_total,
                    scenario_total,
                )
                if comp_metric:
                    metrics.append(comp_metric)

    # Predicted complications
    if not baseline_subset.empty and not scenario_subset.empty:
        predicted_complications = {
            "i_PL_pred": "Prolonged Labor predicted",
            "i_OL_pred": "Obstructed Labor predicted",
            "i_hypoxia_pred": "Hypoxia predicted",
        }
        
        for col, label in predicted_complications.items():
            if col in baseline_subset.columns and col in scenario_subset.columns:
                pred_metric = _format_share_change(
                    label,
                    baseline_subset[col] == 1,
                    scenario_subset[col] == 1,
                    baseline_total,
                    scenario_total,
                )
                if pred_metric:
                    metrics.append(pred_metric)

    return _build_summary(final_metric, metrics)


def _summarize_sdr_delivery(baseline: pd.DataFrame, scenario: pd.DataFrame) -> Dict[str, List[str]]:
    metrics: List[Dict[str, Any]] = []
    baseline_subset = baseline.copy()
    scenario_subset = scenario.copy()
    baseline_total = len(baseline)
    scenario_total = len(scenario)

    final_metric: Optional[Dict[str, Any]] = None
    if "i_mat_death" in baseline.columns and "i_mat_death" in scenario.columns:
        final_metric = _format_count_change(
            "Maternal deaths",
            int(baseline_subset["i_mat_death"].sum()) if "i_mat_death" in baseline_subset.columns else 0,
            int(scenario_subset["i_mat_death"].sum()) if "i_mat_death" in scenario_subset.columns else 0,
            baseline_total,
            scenario_total,
            force=True,
        )

    # ANC coverage for all mothers
    if "i_ANC" in baseline.columns and "i_ANC" in scenario.columns:
        anc_metric = _format_share_change(
            "ANC coverage (all mothers)",
            baseline_subset["i_ANC"] if "i_ANC" in baseline_subset.columns else None,
            scenario_subset["i_ANC"] if "i_ANC" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if anc_metric:
            metrics.append(anc_metric)

    # Initial delivery location insights
    if "i_loc" in baseline.columns and "i_loc" in scenario.columns:
        # Initial L4 deliveries
        init_l4_metric = _format_share_change(
            "Initial deliveries at L4",
            baseline_subset["i_loc"] == 2 if "i_loc" in baseline_subset.columns else None,
            scenario_subset["i_loc"] == 2 if "i_loc" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if init_l4_metric:
            metrics.append(init_l4_metric)

        # Initial L5 deliveries
        init_l5_metric = _format_share_change(
            "Initial deliveries at L5",
            baseline_subset["i_loc"] == 3 if "i_loc" in baseline_subset.columns else None,
            scenario_subset["i_loc"] == 3 if "i_loc" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if init_l5_metric:
            metrics.append(init_l5_metric)

        # Initial L2/L3 deliveries
        init_l2l3_metric = _format_share_change(
            "Initial deliveries at L2/L3",
            baseline_subset["i_loc"] == 1 if "i_loc" in baseline_subset.columns else None,
            scenario_subset["i_loc"] == 1 if "i_loc" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if init_l2l3_metric:
            metrics.append(init_l2l3_metric)

        # Initial home deliveries
        init_home_metric = _format_share_change(
            "Initial deliveries at home",
            baseline_subset["i_loc"] == 0 if "i_loc" in baseline_subset.columns else None,
            scenario_subset["i_loc"] == 0 if "i_loc" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if init_home_metric:
            metrics.append(init_home_metric)

    # Transfer predictions
    if "i_transfer_pred" in baseline.columns and "i_transfer_pred" in scenario.columns:
        transfer_pred_metric = _format_share_change(
            "Transfers predicted early",
            baseline_subset["i_transfer_pred"] if "i_transfer_pred" in baseline_subset.columns else None,
            scenario_subset["i_transfer_pred"] if "i_transfer_pred" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if transfer_pred_metric:
            metrics.append(transfer_pred_metric)

    # Actual transfers
    if "i_transfer_actual" in baseline.columns and "i_transfer_actual" in scenario.columns:
        transfer_actual_metric = _format_share_change(
            "Actual transfers executed",
            baseline_subset["i_transfer_actual"] if "i_transfer_actual" in baseline_subset.columns else None,
            scenario_subset["i_transfer_actual"] if "i_transfer_actual" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if transfer_actual_metric:
            metrics.append(transfer_actual_metric)

    # Final delivery location insights - all locations
    if "i_loc_new_v2" in baseline.columns and "i_loc_new_v2" in scenario.columns:
        # Final L4 deliveries
        final_l4_metric = _format_share_change(
            "Final deliveries at L4",
            baseline_subset["i_loc_new_v2"] == 2 if "i_loc_new_v2" in baseline_subset.columns else None,
            scenario_subset["i_loc_new_v2"] == 2 if "i_loc_new_v2" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if final_l4_metric:
            metrics.append(final_l4_metric)
        
        # Final L5 deliveries
        final_l5_metric = _format_share_change(
            "Final deliveries at L5",
            baseline_subset["i_loc_new_v2"] == 3 if "i_loc_new_v2" in baseline_subset.columns else None,
            scenario_subset["i_loc_new_v2"] == 3 if "i_loc_new_v2" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if final_l5_metric:
            metrics.append(final_l5_metric)

        # Final L2/L3 deliveries
        final_l2l3_metric = _format_share_change(
            "Final deliveries at L2/L3",
            baseline_subset["i_loc_new_v2"] == 1 if "i_loc_new_v2" in baseline_subset.columns else None,
            scenario_subset["i_loc_new_v2"] == 1 if "i_loc_new_v2" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if final_l2l3_metric:
            metrics.append(final_l2l3_metric)

        # Final home deliveries
        final_home_metric = _format_share_change(
            "Final deliveries at home",
            baseline_subset["i_loc_new_v2"] == 0 if "i_loc_new_v2" in baseline_subset.columns else None,
            scenario_subset["i_loc_new_v2"] == 0 if "i_loc_new_v2" in scenario_subset.columns else None,
            baseline_total,
            scenario_total,
        )
        if final_home_metric:
            metrics.append(final_home_metric)

    # Complication deaths
    if "i_comp_death_new" in baseline.columns and "i_comp_death_new" in scenario.columns:
        comp_death_metric = _format_count_change(
            "Complication-related deaths",
            int(baseline_subset["i_comp_death_new"].sum()) if "i_comp_death_new" in baseline_subset.columns else 0,
            int(scenario_subset["i_comp_death_new"].sum()) if "i_comp_death_new" in scenario_subset.columns else 0,
            baseline_total,
            scenario_total,
        )
        if comp_death_metric:
            metrics.append(comp_death_metric)

    return _build_summary(final_metric, metrics)


SUMMARY_BUILDERS = {
    "Risk Stratification & Delivery Location": _summarize_risk_delivery,
    "ANC Care, Complications & Maternal Death": _summarize_anc_pathway,
    "Intrapartum Monitoring & Delivery Mode": _summarize_intrapartum,
    "SDR Delivery Location": _summarize_sdr_delivery,
}

def create_sankey_base(data, stages, stage_labels, title, colors_map=None):
    """
    Base function to create Sankey diagrams
    """
    # Ensure categorical dtype for efficiency
    optimized_data = data.copy()
    for stage in stages:
        if optimized_data[stage].dtype != "category":
            optimized_data[stage] = optimized_data[stage].astype("category")

    # Create all unique labels across stages preserving order of appearance
    unique_labels = []
    seen = set()
    for stage in stages:
        stage_values = optimized_data[stage].cat.categories if isinstance(optimized_data[stage].dtype, CategoricalDtype) else optimized_data[stage].unique()
        for label in stage_values:
            if label not in seen:
                unique_labels.append(label)
                seen.add(label)

    # Create node mapping
    node_dict = {label: i for i, label in enumerate(unique_labels)}
    
    # Create flows between consecutive stages
    source_nodes = []
    target_nodes = []
    values = []
    
    for i in range(len(stages) - 1):
        source_stage = stages[i]
        target_stage = stages[i + 1]

        flow_data = (
            optimized_data.groupby([source_stage, target_stage], observed=True)
            .size()
            .reset_index(name="count")
        )

        for _, row in flow_data.iterrows():
            source_label = row[source_stage]
            target_label = row[target_stage]
            count = row["count"]

            source_nodes.append(node_dict[source_label])
            target_nodes.append(node_dict[target_label])
            values.append(count)
    
    # Calculate node totals
    node_totals = {}
    for stage in stages:
        stage_totals = optimized_data[stage].value_counts(sort=False)
        for label, count in stage_totals.items():
            if label not in node_totals:
                node_totals[label] = count
    
    # Create node labels with totals
    labeled_nodes = []
    for label in unique_labels:
        total = node_totals.get(label, 0)
        labeled_nodes.append(f"{label}\n{total:,}")
    
    # Default colors
    default_colors = [
        'rgba(65, 105, 225, 0.8)',   # Blue
        'rgba(60, 179, 113, 0.8)',   # Green  
        'rgba(220, 20, 60, 0.8)',    # Red
        'rgba(255, 140, 0, 0.8)',    # Orange
        'rgba(138, 43, 226, 0.8)',   # Purple
        'rgba(0, 206, 209, 0.8)',    # Cyan
        'rgba(255, 182, 193, 0.8)',  # Pink
        'rgba(144, 238, 144, 0.8)',  # Light Green
        'rgba(255, 215, 0, 0.8)',    # Gold
        'rgba(128, 128, 128, 0.8)'   # Gray
    ]
    
    # Apply colors
    node_colors = []
    for i, label in enumerate(unique_labels):
        if colors_map and label in colors_map:
            node_colors.append(colors_map[label])
        else:
            node_colors.append(default_colors[i % len(default_colors)])
    
    # Create Sankey diagram
    fig = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labeled_nodes,
            color=node_colors
        ),
        link=dict(
            source=source_nodes,
            target=target_nodes,
            value=values,
            color='rgba(128, 128, 128, 0.2)',
            hovertemplate='%{source.label} → %{target.label}<br>Flow: %{value:,} (%{customdata:.1f}%)<extra></extra>',
            customdata=[round((val / node_totals[unique_labels[src]] * 100), 1) for val, src in zip(values, source_nodes)]
        )
    ))
    
    fig.update_layout(
        title_text=title,
        font_size=12,
        font_color="black",
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=700,
        width=1400,
        title_font_size=16,
        title_x=0.5,
        title_xanchor='center'
    )
    
    # Improve rendering quality
    fig.update_traces(
        textfont_size=11,
        textfont_color="black"
    )
    
    return fig

def create_risk_delivery_pathway(df, title_suffix=""):
    """
    Create risk stratification and delivery location pathway
    """
    n = len(df)
    stage1 = pd.Categorical(np.repeat("Mothers", n))
    stage2 = pd.Categorical(df["i_pocus"].map({0: "No POCUS", 1: "POCUS"}))
    stage3 = pd.Categorical(df["i_risk"].map({0: "Low Risk", 1: "High Risk"}))
    stage4 = pd.Categorical(df["i_risk_pred"].map({0: "Low Risk Predicted", 1: "High Risk Predicted"}))
    stage5 = pd.Categorical(df["i_loc"].map({0: "Home", 1: "L2/L3", 2: "L4", 3: "L5"}))

    data = pd.DataFrame({
        "Stage1": stage1,
        "Stage2": stage2,
        "Stage3": stage3,
        "Stage4": stage4,
        "Stage5": stage5,
    })

    # Define colors for all possible values
    colors_map = {
        'Mothers': 'rgba(65, 105, 225, 0.8)',
        'Low Risk': 'rgba(144, 238, 144, 0.8)',
        'High Risk': 'rgba(255, 140, 0, 0.8)',
        'No POCUS': 'rgba(205, 70, 0, 0.5)',
        'POCUS': 'rgba(255, 70, 0, 0.8)',
        'Low Risk Predicted': 'rgba(60, 179, 113, 0.8)',
        'High Risk Predicted': 'rgba(220, 20, 60, 0.8)',
        'Home': 'rgba(255, 182, 193, 0.8)',
        'L2/L3': 'rgba(0, 206, 209, 0.8)',
        'L4': 'rgba(255, 215, 0, 0.8)',
        'L5': 'rgba(138, 43, 226, 0.4)'
    }
    
    stages = ['Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5']
    title = f"Risk Stratification and Delivery Location Pathway{title_suffix}<br>Total Population: {n:,}"
    
    return create_sankey_base(data, stages, None, title, colors_map)

def create_ANC_maternal_death_pathway(df, title_suffix=""):
    """
    Create ANC care, complications, and maternal death pathway
    """
    stage2 = df["i_ANC"].map({0: "No ANC", 1: "ANC"})
    stage3 = df["i_anemia"].map({0: "No Anemia", 1: "Anemia"})

    complication_labels = np.full(len(df), None, dtype=object)
    complication_labels[df["i_pph"] == 1] = "PPH"
    complication_labels[df["i_OL"] == 1] = "Obstructed Labor"
    complication_labels[df["i_PL"] == 1] = "Prolonged Labor"
    complication_labels[df["i_eclampsia"] == 1] = "Eclampsia"
    complication_labels[df["i_mat_sepsis"] == 1] = "Sepsis"
    complication_labels[df["i_hypoxia"] == 1] = "Hypoxia"

    valid_mask = pd.notna(complication_labels)

    stage1 = pd.Categorical(np.repeat("Mothers", valid_mask.sum()))
    stage2 = pd.Categorical(stage2[valid_mask])
    stage3 = pd.Categorical(stage3[valid_mask])
    stage4 = pd.Categorical(complication_labels[valid_mask])
    stage5 = pd.Categorical(df.loc[valid_mask, "i_mat_death"].map({0: "Survived", 1: "Maternal Death"}))

    data_complications = pd.DataFrame({
        "Stage1": stage1,
        "Stage2": stage2,
        "Stage3": stage3,
        "Stage4": stage4,
        "Stage5": stage5,
    })

    # Define colors
    colors_map = {
        'Mothers': 'rgba(65, 105, 225, 0.8)',
        'ANC': 'rgba(60, 179, 113, 0.8)',
        'No ANC': 'rgba(100, 20, 60, 0.8)',
        'Anemia': 'rgba(255, 140, 0, 0.8)',
        'No Anemia': 'rgba(138, 43, 226, 0.8)',
        'PPH': 'rgba(0, 206, 209, 0.8)',
        'Obstructed Labor': 'rgba(255, 182, 193, 0.8)',
        'Prolonged Labor': 'rgba(147, 112, 219, 0.8)',
        'Hypoxia': 'rgba(255, 99, 71, 0.8)',
        'Eclampsia': 'rgba(144, 238, 144, 0.8)',
        'Sepsis': 'rgba(255, 192, 203, 0.8)',
        'Survived': 'rgba(60, 179, 113, 0.8)',
        'Maternal Death': 'rgba(220, 20, 60, 0.8)'
    }
    
    stages = ['Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5']
    title = f"ANC Care, Complications, and Maternal Death Pathway{title_suffix}<br>Cases with Complications: {len(data_complications):,}"
    
    return create_sankey_base(data_complications, stages, None, title, colors_map)

def create_intrapartum_pathway(df, title_suffix=""):
    """
    Intrapartum monitoring and delivery mode pathway
    """
    valid_mask = df["i_mod"].notna()
    valid_df = df.loc[valid_mask]

    stage1 = pd.Categorical(np.repeat("Mothers", valid_mask.sum()))
    stage2 = pd.Categorical(valid_df["i_loc"].map({0: "Home", 1: "L2/L3", 2: "L4", 3: "L5"}))
    stage3 = pd.Categorical(valid_df["i_sensors"].map({0: "No Sensors", 1: "Sensors"}))

    actual_complication = np.full(valid_df.shape[0], "No Leading Complication", dtype=object)
    actual_complication[valid_df["i_PL"] == 1] = "Prolonged Labor"
    actual_complication[valid_df["i_OL"] == 1] = "Obstructed Labor"
    actual_complication[valid_df["i_hypoxia"] == 1] = "Hypoxia"

    predicted_complication = np.full(valid_df.shape[0], "No Complication Predicted", dtype=object)
    predicted_complication[valid_df["i_PL_pred"] == 1] = "Prolonged Labor Predicted"
    predicted_complication[valid_df["i_OL_pred"] == 1] = "Obstructed Labor Predicted"
    predicted_complication[valid_df["i_hypoxia_pred"] == 1] = "Hypoxia Predicted"

    stage4 = pd.Categorical(actual_complication)
    stage5 = pd.Categorical(predicted_complication)
    stage6 = pd.Categorical(valid_df["i_mod"].map({
        'SVD': 'Spontaneous Vaginal Delivery', 
        'AVD': 'Assisted Vaginal Delivery', 
        'EmCS': 'Emergency Cesarean', 
        'ELCS': 'Elective Cesarean'
    }))
    stage7 = pd.Categorical(valid_df["i_unnecessary_cs"].map({0: 'Necessary', 1: 'Unnecessary CS'}))

    data = pd.DataFrame({
        "Stage1": stage1,
        "Stage2": stage2,
        "Stage3": stage3,
        "Stage4": stage4,
        "Stage5": stage5,
        "Stage6": stage6,
        "Stage7": stage7,
    })
    
    colors_map = {
        'Mothers': 'rgba(65, 105, 225, 0.8)',
        'Home': 'rgba(255, 182, 193, 0.8)',
        'L2/L3': 'rgba(0, 206, 209, 0.8)',
        'L4': 'rgba(255, 215, 0, 0.8)',
        'L5': 'rgba(138, 43, 226, 0.4)',
        'Prolonged Labor': 'rgba(144, 238, 144, 0.8)',
        'Obstructed Labor': 'rgba(255, 140, 0, 0.8)',
        'Hypoxia': 'rgba(255, 99, 71, 0.8)',
        'No Leading Complication': 'rgba(200, 200, 200, 0.8)',
        'No Sensors': 'rgba(180, 180, 180, 0.8)',
        'Sensors': 'rgba(100, 149, 237, 0.8)',
        'Prolonged Labor Predicted': 'rgba(144, 238, 144, 0.6)',
        'Obstructed Labor Predicted': 'rgba(255, 140, 0, 0.6)',
        'Hypoxia Predicted': 'rgba(255, 99, 71, 0.6)',
        'No Complication Predicted': 'rgba(200, 200, 200, 0.6)',
        'No Transfer Predicted': 'rgba(138, 43, 226, 0.8)',
        'Transfer Predicted': 'rgba(0, 206, 209, 0.8)',
        'Necessary': 'rgba(55, 210, 0, 0.8)', 
        'Unnecessary CS': 'rgba(255, 15, 0, 0.8)',
        'Assisted Vaginal Delivery': 'rgba(255, 140, 0, 0.8)',
        'Elective Cesarean': 'rgba(205, 140, 0, 0.8)',
        'Emergency Cesarean': 'rgba(155, 140, 0, 0.8)',
        'Spontaneous Vaginal Delivery': 'rgba(25, 140, 0, 0.8)',
    }
    
    stages = ['Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5', 'Stage6', 'Stage7']
    title = f"Intrapartum Monitoring and Delivery Mode Pathway{title_suffix}<br>Total Population: {len(data):,}"
    
    return create_sankey_base(data, stages, None, title, colors_map)

def create_SDR_delivery_pathway(df, title_suffix=""):
    """
    SDR delivery location pathway
    """
    n = len(df)

    stage1 = pd.Categorical(np.repeat("Mothers", n))
    stage2 = pd.Categorical(df["i_ANC"].map({0: "No ANC", 1: "ANC"}))
    stage3 = pd.Categorical(df["i_loc"].map({0: "Home", 1: "L2/L3", 2: "L4", 3: "L5"}))
    stage4 = pd.Categorical(df["i_transfer_pred"].map({0: "No Transfer Predicted", 1: "1st Transfer for Emergency C-Section"}))

    if "i_loc_new_v1" in df.columns:
        stage5 = pd.Categorical(df["i_loc_new_v1"].map({0: 'Home v1', 1: 'L2/L3 v1', 2: 'L4 v1', 3: 'L5 v1'}))
    else:
        stage5 = pd.Categorical(df["i_loc"].map({0: 'Home v1', 1: 'L2/L3 v1', 2: 'L4 v1', 3: 'L5 v1'}))

    stage6 = pd.Categorical(df["i_transfer_actual"].map({0: 'No Actual Transfer', 1: '2nd Transfer for Complication Treatment'}))

    if "i_loc_new_v2" in df.columns:
        stage7 = pd.Categorical(df["i_loc_new_v2"].map({0: 'Home Final', 1: 'L2/L3 Final', 2: 'L4 Final', 3: 'L5 Final'}))
    else:
        stage7 = pd.Categorical(df["i_loc"].map({0: 'Home Final', 1: 'L2/L3 Final', 2: 'L4 Final', 3: 'L5 Final'}))

    if "i_comp_death_new" in df.columns:
        stage8 = pd.Categorical(df["i_comp_death_new"].map({0: 'No Complication Death', 1: 'Complication Death'}))
    else:
        complication_death = (
            (_column_or_zeros(df, 'i_pph') == 1)
            | (_column_or_zeros(df, 'i_OL') == 1)
            | (_column_or_zeros(df, 'i_eclampsia') == 1)
            | (_column_or_zeros(df, 'i_mat_sepsis') == 1)
        )
        complication_death_series = pd.Series(complication_death, index=df.index)
        stage8 = pd.Categorical(complication_death_series.map({False: 'No Complication Death', True: 'Complication Death'}))

    stage9 = pd.Categorical(df["i_mat_death"].map({0: 'Survived', 1: 'Maternal Death'}))

    data = pd.DataFrame({
        "Stage1": stage1,
        "Stage2": stage2,
        "Stage3": stage3,
        "Stage4": stage4,
        "Stage5": stage5,
        "Stage6": stage6,
        "Stage7": stage7,
        "Stage8": stage8,
        "Stage9": stage9,
    })
    
    colors_map = {
        'Mothers': 'rgba(65, 105, 225, 0.8)',
        'No ANC': 'rgba(100, 20, 60, 0.8)',
        'ANC': 'rgba(60, 179, 113, 0.8)',
        'Home': 'rgba(255, 182, 193, 0.8)',
        'L2/L3': 'rgba(0, 206, 209, 0.8)',
        'L4': 'rgba(255, 215, 0, 0.8)',
        'L5': 'rgba(138, 43, 226, 0.4)',
        'Home v1': 'rgba(255, 182, 193, 0.7)',
        'L2/L3 v1': 'rgba(0, 206, 209, 0.7)',
        'L4 v1': 'rgba(255, 215, 0, 0.7)',
        'L5 v1': 'rgba(138, 43, 226, 0.3)',
        'Home Final': 'rgba(255, 182, 193, 0.9)',
        'L2/L3 Final': 'rgba(0, 206, 209, 0.9)',
        'L4 Final': 'rgba(255, 215, 0, 0.9)',
        'L5 Final': 'rgba(138, 43, 226, 0.5)',
        'No Transfer Predicted': 'rgba(138, 43, 226, 0.8)',
        '1st Transfer for Emergency C-Section': 'rgba(255, 140, 0, 0.8)',
        'No Actual Transfer': 'rgba(144, 238, 144, 0.8)',
        '2nd Transfer for Complication Treatment': 'rgba(255, 99, 71, 0.8)',
        'No Complication Death': 'rgba(60, 179, 113, 0.8)',
        'Complication Death': 'rgba(255, 140, 0, 0.8)',
        'Survived': 'rgba(60, 179, 113, 0.8)',
        'Maternal Death': 'rgba(220, 20, 60, 0.8)'
    }
    
    stages = ['Stage1', 'Stage2', 'Stage3', 'Stage4', 'Stage5', 'Stage6', 'Stage7', 'Stage8', 'Stage9']
    title = f"SDR Delivery Location Pathway{title_suffix}<br>Total Population: {len(data):,}"
    
    return create_sankey_base(data, stages, None, title, colors_map)

# Pathway mapping for easy selection
PATHWAY_FUNCTIONS = {
    "Risk Stratification & Delivery Location": create_risk_delivery_pathway,
    "ANC Care, Complications & Maternal Death": create_ANC_maternal_death_pathway,
    "Intrapartum Monitoring & Delivery Mode": create_intrapartum_pathway,
    "SDR Delivery Location": create_SDR_delivery_pathway
}

def generate_sankey_comparison(baseline_data, scenario_data, pathway_name):
    """
    Generate side-by-side Sankey diagrams for baseline vs scenario comparison
    """
    if pathway_name not in PATHWAY_FUNCTIONS:
        raise ValueError(f"Unknown pathway: {pathway_name}")
    
    pathway_func = PATHWAY_FUNCTIONS[pathway_name]
    
    # Generate baseline diagram
    fig_baseline = pathway_func(baseline_data, " - Baseline")
    
    # Generate scenario diagram  
    fig_scenario = pathway_func(scenario_data, " - Scenario")
    
    summary_builder = SUMMARY_BUILDERS.get(pathway_name)
    if summary_builder:
        summary = summary_builder(baseline_data, scenario_data)
    else:
        summary = _select_headline_and_bullets([])
    
    return fig_baseline, fig_scenario, summary
