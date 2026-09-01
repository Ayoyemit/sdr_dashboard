import { ScenarioResult } from "./scenarios";

function lastValue(series: number[] | undefined): number | null {
  if (!series?.length) return null;
  return series[series.length - 1] ?? null;
}

export function endOfRunL45DeliveryPercent(result: ScenarioResult): number {
  const d = result.timeseries.delivery_location.intervention;
  const last = d.l4.length - 1;
  return Math.round((d.l4[last] ?? 0) + (d.l5[last] ?? 0));
}

export function endOfRunIndicatorPercent(
  result: ScenarioResult,
  key: "anc_rate_per_100_lb" | "cs_rate_per_100_lb" | "normal_referral_per_100_lb" | "high_risk_per_100_lb",
  arm: "baseline" | "intervention" = "intervention"
): number | null {
  const bundle = result.timeseries.indicator_series?.[key];
  if (!bundle) return null;
  const value = lastValue(bundle[arm]);
  return value != null ? Math.round(value) : null;
}

export function formatKakamegaCostUsd(
  amountUsd: number,
  county: string,
  naLabel: string
): string {
  if (county !== "kakamega") return naLabel;
  return `$${amountUsd.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

/** @deprecated Use formatKakamegaCostUsd */
export function formatCostDalyUsd(
  costPerDaly: number,
  county: string,
  naLabel: string
): string {
  return formatKakamegaCostUsd(costPerDaly, county, naLabel);
}
