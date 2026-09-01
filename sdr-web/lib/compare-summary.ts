import { TranslateFn } from "./i18n";
import {
  endOfRunIndicatorPercent,
  endOfRunL45DeliveryPercent,
  formatKakamegaCostUsd,
} from "./run-metrics";
import { CompareResponse, ScenarioResult, SupportedCountyId } from "./scenarios";

export type CompareWinner = "a" | "b" | "tie" | "tradeoff";

export interface CompareMetricRow {
  id: string;
  label: string;
  valueA: string;
  valueB: string;
  rawA: number;
  rawB: number;
  winner: CompareWinner;
  winnerLabel: string;
  higherIsBetter: boolean;
}

export interface CompareMetricSection {
  id: string;
  titleKey: string;
  rows: CompareMetricRow[];
}

function fmtNum(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function fmtPct(n: number | null): string {
  if (n == null) return "—";
  return `${n}%`;
}

function winnerLabel(
  w: CompareWinner,
  nameA: string,
  nameB: string,
  t: TranslateFn
): string {
  if (w === "a") return nameA;
  if (w === "b") return nameB;
  if (w === "tie") return t("compare.tie");
  return t("compare.tradeoff");
}

function pickWinner(a: number, b: number, higherIsBetter: boolean): CompareWinner {
  if (a === b) return "tie";
  if (higherIsBetter) return b > a ? "b" : "a";
  return b < a ? "b" : "a";
}

function withWinnerLabels(
  rows: Omit<CompareMetricRow, "winnerLabel">[],
  nameA: string,
  nameB: string,
  t: TranslateFn
): CompareMetricRow[] {
  return rows.map((row) => ({
    ...row,
    winnerLabel: winnerLabel(row.winner, nameA, nameB, t),
  }));
}

function row(
  id: string,
  label: string,
  rawA: number,
  rawB: number,
  valueA: string,
  valueB: string,
  higherIsBetter: boolean
): Omit<CompareMetricRow, "winnerLabel"> {
  return {
    id,
    label,
    valueA,
    valueB,
    rawA,
    rawB,
    winner: pickWinner(rawA, rawB, higherIsBetter),
    higherIsBetter,
  };
}

export function buildCompareMetricSections(
  a: ScenarioResult,
  b: ScenarioResult,
  nameA: string,
  nameB: string,
  county: SupportedCountyId,
  t: TranslateFn
): CompareMetricSection[] {
  const sa = a.summary;
  const sb = b.summary;
  const costNa = t("exec.costDalyNa");

  const healthRows = withWinnerLabels(
    [
      row(
        "deaths",
        t("compare.metricDeaths"),
        sa.maternal_deaths_averted,
        sb.maternal_deaths_averted,
        fmtNum(sa.maternal_deaths_averted),
        fmtNum(sb.maternal_deaths_averted),
        true
      ),
      row(
        "complications",
        t("compare.metricComplications"),
        sa.severe_maternal_outcomes_averted,
        sb.severe_maternal_outcomes_averted,
        fmtNum(sa.severe_maternal_outcomes_averted),
        fmtNum(sb.severe_maternal_outcomes_averted),
        true
      ),
    ],
    nameA,
    nameB,
    t
  );

  const ancA = endOfRunIndicatorPercent(a, "anc_rate_per_100_lb");
  const ancB = endOfRunIndicatorPercent(b, "anc_rate_per_100_lb");
  const highRiskA = endOfRunIndicatorPercent(a, "high_risk_per_100_lb");
  const highRiskB = endOfRunIndicatorPercent(b, "high_risk_per_100_lb");
  const csA = endOfRunIndicatorPercent(a, "cs_rate_per_100_lb");
  const csB = endOfRunIndicatorPercent(b, "cs_rate_per_100_lb");
  const refA = endOfRunIndicatorPercent(a, "normal_referral_per_100_lb");
  const refB = endOfRunIndicatorPercent(b, "normal_referral_per_100_lb");
  const l45A = endOfRunL45DeliveryPercent(a);
  const l45B = endOfRunL45DeliveryPercent(b);

  const processRows = withWinnerLabels(
    [
      row("anc_rate", t("compare.metricAncRate"), ancA ?? 0, ancB ?? 0, fmtPct(ancA), fmtPct(ancB), true),
      row(
        "high_risk",
        t("compare.metricHighRisk"),
        highRiskA ?? 0,
        highRiskB ?? 0,
        fmtPct(highRiskA),
        fmtPct(highRiskB),
        true
      ),
      row(
        "l45_delivery",
        t("compare.metricL45Delivery"),
        l45A,
        l45B,
        fmtPct(l45A),
        fmtPct(l45B),
        true
      ),
      row("cs_rate", t("compare.metricCsRate"), csA ?? 0, csB ?? 0, fmtPct(csA), fmtPct(csB), true),
      row(
        "normal_referral",
        t("compare.metricReferral"),
        refA ?? 0,
        refB ?? 0,
        fmtPct(refA),
        fmtPct(refB),
        true
      ),
    ],
    nameA,
    nameB,
    t
  );

  const costRows = withWinnerLabels(
    [
      row(
        "total_cost",
        t("compare.metricTotalCost"),
        county === "kakamega" ? sa.cumulative_cost_usd : 0,
        county === "kakamega" ? sb.cumulative_cost_usd : 0,
        formatKakamegaCostUsd(sa.cumulative_cost_usd, county, costNa),
        formatKakamegaCostUsd(sb.cumulative_cost_usd, county, costNa),
        false
      ),
    ],
    nameA,
    nameB,
    t
  );

  return [
    { id: "health", titleKey: "compare.sectionHealthOutcomes", rows: healthRows },
    { id: "process", titleKey: "compare.sectionProcess", rows: processRows },
    { id: "cost", titleKey: "compare.sectionCost", rows: costRows },
  ];
}

/** @deprecated Use buildCompareMetricSections — kept for any legacy callers */
export function buildCompareMetricRows(
  a: ScenarioResult,
  b: ScenarioResult,
  nameA: string,
  nameB: string,
  t: TranslateFn
): CompareMetricRow[] {
  return buildCompareMetricSections(a, b, nameA, nameB, "kakamega", t).flatMap((s) => s.rows);
}

export interface CompareVerdict {
  headline: string;
  deathsWinner: CompareWinner;
  valueWinner: CompareWinner;
}

export function buildCompareVerdict(
  data: CompareResponse,
  sections: CompareMetricSection[],
  t: TranslateFn
): CompareVerdict {
  const { scenario_a: sa, scenario_b: sb, result_a: a, result_b: b } = data;
  if (!a || !b) {
    return { headline: "", deathsWinner: "tie", valueWinner: "tie" };
  }

  const allRows = sections.flatMap((s) => s.rows);
  const deathsRow = allRows.find((r) => r.id === "deaths");
  const totalCostRow = allRows.find((r) => r.id === "total_cost");
  if (!deathsRow || !totalCostRow) {
    return {
      headline: t("compare.verdictDefault", { a: sa.name, b: sb.name }),
      deathsWinner: "tie",
      valueWinner: "tie",
    };
  }

  const deathsWinner = deathsRow.winner;
  const valueWinner =
    totalCostRow.winner === deathsRow.winner ? totalCostRow.winner : "tradeoff";

  let headline: string;
  if (deathsWinner === "tie" && totalCostRow.winner === "tie") {
    headline = t("compare.verdictSimilar", { a: sa.name, b: sb.name });
  } else if (
    deathsWinner === totalCostRow.winner &&
    deathsWinner !== "tie" &&
    deathsWinner !== "tradeoff"
  ) {
    const winnerName = deathsWinner === "a" ? sa.name : sb.name;
    headline = t("compare.verdictAllRound", { winner: winnerName });
  } else if (
    deathsWinner !== "tie" &&
    totalCostRow.winner !== "tie" &&
    deathsWinner !== totalCostRow.winner
  ) {
    const healthName = deathsWinner === "a" ? sa.name : sb.name;
    const valueName = totalCostRow.winner === "a" ? sa.name : sb.name;
    headline = t("compare.verdictTradeoff", { health: healthName, value: valueName });
  } else {
    headline = t("compare.verdictDefault", { a: sa.name, b: sb.name });
  }

  return { headline, deathsWinner, valueWinner };
}
