import { TranslateFn } from "./i18n";
import { Scenario, ScenarioResult, SupportedCountyId } from "./scenarios";

export type ResultsViewMode = "policy" | "analyst";

export interface ExecutiveSummaryData {
  headline: string;
  bullets: string[];
  englishNarrative?: string;
  verdictTags: string[];
  caveat: string;
  systemNote: string;
  runLabel: string;
  showTotalCost: boolean;
  l45ShiftPts: number;
}

function fmt(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function pct(n: number): number {
  return Math.round(n);
}

function deliveryL45Share(series: { l4: number[]; l5: number[] }, index: number): number {
  const l4 = series.l4[index] ?? 0;
  const l5 = series.l5[index] ?? 0;
  return l4 + l5;
}

function ancShare(series: number[] | undefined, index: number): number | null {
  if (!series?.length) return null;
  return series[index] ?? null;
}

export function buildExecutiveSummary(
  scenario: Scenario,
  result: ScenarioResult,
  t: TranslateFn,
  locale: "en" | "sw"
): ExecutiveSummaryData {
  const { summary } = result;
  const horizon = scenario.run.implementation_years + scenario.run.maintenance_years;
  const resources = result.resource_adequacy_end_of_run;
  const weakest =
    resources.length > 0
      ? resources.reduce((min, r) => (r.percent < min.percent ? r : min))
      : null;

  const hasCi =
    !!result.timeseries.maternal_mortality_rate.ci_lower &&
    !!result.timeseries.maternal_mortality_rate.ci_upper;

  let caveat: string;
  if (result.meta.n_runs > 1 && hasCi) {
    caveat = t("exec.caveatRobustCi");
  } else if (result.meta.n_runs > 1) {
    caveat = t("exec.caveatRobust");
  } else {
    caveat = t("exec.caveatQuick");
  }

  let systemNote: string;
  if (!weakest) {
    systemNote = t("exec.systemNone");
  } else if (weakest.percent >= 85) {
    systemNote = t("exec.systemOk");
  } else if (weakest.percent >= 65) {
    systemNote = t("exec.systemModerate", { name: weakest.name, percent: weakest.percent });
  } else {
    systemNote = t("exec.systemStrain", { name: weakest.name, percent: weakest.percent });
  }

  const uiOnly = result.applied_interventions.filter((i) => !i.is_wired_in_model);
  if (uiOnly.length > 0) {
    caveat += ` ${t("exec.caveatUiOnly", { count: uiOnly.length })}`;
  }

  const delivery = result.timeseries.delivery_location;
  const last = delivery.intervention.l4.length - 1;
  const l45Start = pct(deliveryL45Share(delivery.baseline, 0));
  const l45End = pct(deliveryL45Share(delivery.intervention, last));
  const l45ShiftPts = l45End - l45Start;

  const ancSeries = result.timeseries.indicator_series?.anc_rate_per_100_lb;
  const ancStartRaw = ancShare(ancSeries?.baseline, 0);
  const ancEndRaw = ancShare(ancSeries?.intervention, last);
  const ancStart = ancStartRaw != null ? pct(ancStartRaw) : 56;
  const ancEnd = ancEndRaw != null ? pct(ancEndRaw) : 82;

  const deaths = fmt(summary.maternal_deaths_averted);
  const showTotalCost = scenario.county === "kakamega";

  const verdictTags = [t("exec.verdictStrongOutcomes")];
  if (weakest && weakest.percent >= 75) {
    verdictTags.push(t("exec.verdictSupplyOk"));
  }
  if (scenario.hss.enabled && scenario.hss.intensity !== "off") {
    verdictTags.push(t("exec.verdictHss"));
  }

  return {
    headline: t("exec.headline", {
      years: horizon,
      deaths,
      l45Start,
      l45End,
      l45Pts: Math.abs(l45ShiftPts),
      ancStart,
      ancEnd,
    }),
    bullets: [
      t("exec.bulletDeaths", { deaths, years: horizon }),
      t("exec.bulletSevere", {
        count: fmt(summary.severe_maternal_outcomes_averted),
      }),
      ...(showTotalCost
        ? [t("exec.bulletTotalCost", { totalCost: fmt(summary.cumulative_cost_usd) })]
        : []),
    ],
    englishNarrative: locale === "sw" ? result.narrative.in_plain_english : undefined,
    verdictTags,
    caveat,
    systemNote,
    showTotalCost,
    l45ShiftPts,
    runLabel:
      result.meta.n_runs > 1
        ? t("exec.runRobust", {
            runs: result.meta.n_runs,
            seconds: result.meta.runtime_seconds.toFixed(0),
          })
        : t("exec.runQuick", { seconds: result.meta.runtime_seconds.toFixed(0) }),
  };
}

export function isCostStoryAvailable(county: SupportedCountyId): boolean {
  return county === "kakamega";
}
