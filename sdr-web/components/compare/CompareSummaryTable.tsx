"use client";

import { useMemo } from "react";
import ResponsiveDataView from "@/components/responsive/ResponsiveDataView";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { buildCompareMetricRows, buildCompareVerdict, CompareMetricRow } from "@/lib/compare-summary";
import { CompareResponse } from "@/lib/scenarios";

interface Props {
  data: CompareResponse;
}

function WinnerBadge({
  winner,
  label,
}: {
  winner: "a" | "b" | "tie" | "tradeoff";
  label: string;
}) {
  const styles =
    winner === "a"
      ? "bg-blue-50/80 text-[#2563A8] border-[#2563A8]/25"
      : winner === "b"
        ? "bg-emerald-50/80 text-[#2B7A3E] border-[#2B7A3E]/25"
        : winner === "tradeoff"
          ? "bg-warning/10 text-warning border-warning/30"
          : "bg-paper-deep text-ink-muted border-border";

  return (
    <span className={`inline-block text-[11px] px-2 py-0.5 rounded border ${styles}`}>
      {label}
    </span>
  );
}

function DesktopTable({
  rows,
  scenarioAName,
  scenarioBName,
}: {
  rows: CompareMetricRow[];
  scenarioAName: string;
  scenarioBName: string;
}) {
  const { t } = useLocale();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-[11px] uppercase tracking-wider text-ink-muted">
            <th className="px-6 py-3 font-medium min-w-[180px]">{t("compare.metric")}</th>
            <th className="px-4 py-3 font-medium min-w-[120px]" style={{ color: "#2563A8" }}>
              {scenarioAName}
            </th>
            <th className="px-4 py-3 font-medium min-w-[120px]" style={{ color: "#2B7A3E" }}>
              {scenarioBName}
            </th>
            <th className="px-6 py-3 font-medium min-w-[140px]">{t("compare.edge")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-border-soft last:border-0">
              <td className="px-6 py-3.5 text-ink-soft">{row.label}</td>
              <td
                className={`px-4 py-3.5 num ${row.winner === "a" ? "font-semibold text-ink" : "text-ink-muted"}`}
              >
                {row.valueA}
              </td>
              <td
                className={`px-4 py-3.5 num ${row.winner === "b" ? "font-semibold text-ink" : "text-ink-muted"}`}
              >
                {row.valueB}
              </td>
              <td className="px-6 py-3.5">
                <WinnerBadge winner={row.winner} label={row.winnerLabel} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MobileCards({
  rows,
  scenarioAName,
  scenarioBName,
}: {
  rows: CompareMetricRow[];
  scenarioAName: string;
  scenarioBName: string;
}) {
  return (
    <div className="divide-y divide-border-soft">
      {rows.map((row) => (
        <article key={row.id} className="px-4 py-4">
          <h3 className="text-sm font-medium text-ink mb-3">{row.label}</h3>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="rounded-lg border border-[#C0D5E8] bg-[#F4F8FC] p-3">
              <div className="text-[10px] uppercase tracking-wider text-[#2563A8] mb-1 truncate">
                {scenarioAName}
              </div>
              <div
                className={`num text-lg ${row.winner === "a" ? "font-semibold text-ink" : "text-ink-muted"}`}
              >
                {row.valueA}
              </div>
            </div>
            <div className="rounded-lg border border-[#BFDEC4] bg-[#F2FAF4] p-3">
              <div className="text-[10px] uppercase tracking-wider text-[#2B7A3E] mb-1 truncate">
                {scenarioBName}
              </div>
              <div
                className={`num text-lg ${row.winner === "b" ? "font-semibold text-ink" : "text-ink-muted"}`}
              >
                {row.valueB}
              </div>
            </div>
          </div>
          <WinnerBadge winner={row.winner} label={row.winnerLabel} />
        </article>
      ))}
    </div>
  );
}

export default function CompareSummaryTable({ data }: Props) {
  const { t } = useLocale();
  const { result_a: a, result_b: b, scenario_a, scenario_b } = data;

  const rows = useMemo(() => {
    if (!a || !b) return [];
    return buildCompareMetricRows(a, b, scenario_a.name, scenario_b.name, t);
  }, [a, b, scenario_a.name, scenario_b.name, t]);

  const verdict = useMemo(() => buildCompareVerdict(data, rows, t), [data, rows, t]);

  if (!a || !b) return null;

  return (
    <section className="mb-10 bg-card border border-border rounded-xl overflow-hidden">
      <div className="px-4 md:px-6 py-5 border-b border-border bg-paper-deep/40">
        <div className="text-[11px] uppercase tracking-[0.2em] text-accent mb-1">
          {t("compare.tableHeading")}
        </div>
        <h2 className="font-display text-lg sm:text-xl mb-2">{t("compare.tableTitle")}</h2>
        <p className="text-ink-soft text-sm leading-relaxed max-w-3xl">{verdict.headline}</p>
      </div>

      <ResponsiveDataView
        mobileView={
          <MobileCards
            rows={rows}
            scenarioAName={scenario_a.name}
            scenarioBName={scenario_b.name}
          />
        }
      >
        <DesktopTable
          rows={rows}
          scenarioAName={scenario_a.name}
          scenarioBName={scenario_b.name}
        />
      </ResponsiveDataView>

      <div className="px-4 md:px-6 py-4 bg-paper-deep/30 border-t border-border-soft">
        <div className="text-[11px] uppercase tracking-wider text-ink-muted mb-2">
          {t("compare.briefing")}
        </div>
        <ul className="text-xs text-ink-soft space-y-1">
          {verdict.bullets.map((bullet) => (
            <li key={bullet}>• {bullet}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
