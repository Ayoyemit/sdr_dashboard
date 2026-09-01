"use client";

import Link from "next/link";
import BackToLastComparisonLink from "@/components/BackToLastComparisonLink";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { countyDisplayName } from "@/lib/counties";
import { getScenarioHorizonYears, getScenarioPackageItems } from "@/lib/scenario-summary";
import { Scenario } from "@/lib/scenarios";

interface Props {
  scenario: Scenario;
  running: boolean;
  error: string | null;
  onNameChange: (name: string) => void;
  onRun: () => void;
}

function SummaryBody({
  scenario,
  onNameChange,
}: {
  scenario: Scenario;
  onNameChange: (name: string) => void;
}) {
  const { t } = useLocale();
  const items = getScenarioPackageItems(scenario);
  const horizonYears = getScenarioHorizonYears(scenario);
  const wiredCount = items.filter((i) => i.wired).length;
  const uiOnlyCount = items.filter((i) => !i.wired).length;

  return (
    <>
      <input
        type="text"
        value={scenario.name}
        onChange={(e) => onNameChange(e.target.value)}
        className="w-full bg-paper/10 border border-paper/20 rounded px-3 py-2 text-sm mb-4 min-h-[44px]"
        aria-label="Scenario name"
      />

      <div className="text-xs text-paper/60 mb-3 uppercase tracking-wider">{t("common.vsBaseline")}</div>
      <p className="text-sm text-paper/80 mb-4 leading-relaxed">
        {t("design.vsBaseline", {
          years: horizonYears,
          county: countyDisplayName(scenario.county),
        })}
      </p>

      <div className="mb-4">
        <div className="text-xs text-paper/60 mb-2 uppercase tracking-wider">
          {t("design.activeInterventions", { count: items.length })}
        </div>
        <ul className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
          {items.map((item) => (
            <li
              key={`${item.label}-${item.detail ?? ""}`}
              className="flex items-start justify-between gap-2 text-sm text-paper/90"
            >
              <span>{item.label}</span>
              <span className="text-[10px] shrink-0 text-paper/50">
                {item.detail ?? (item.wired ? t("common.wired") : t("common.uiOnly"))}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <dl className="text-sm space-y-2 text-paper/80 border-t border-paper/10 pt-4">
        <div className="flex justify-between gap-2">
          <dt className="text-paper/60">{t("design.horizon")}</dt>
          <dd className="num text-right">
            {t("design.implMaintShort", {
              impl: scenario.run.implementation_years,
              maint: scenario.run.maintenance_years,
            })}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-paper/60">{t("design.runModeLabel")}</dt>
          <dd className="capitalize">{scenario.run.mode}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-paper/60">{t("design.wiredInModel")}</dt>
          <dd className="num">{wiredCount}</dd>
        </div>
        {uiOnlyCount > 0 && (
          <div className="flex justify-between gap-2">
            <dt className="text-paper/60">{t("common.uiOnly")}</dt>
            <dd className="num text-amber-200">{uiOnlyCount}</dd>
          </div>
        )}
      </dl>
    </>
  );
}

export function ScenarioSummaryCompact({
  scenario,
  onNameChange,
}: {
  scenario: Scenario;
  onNameChange: (name: string) => void;
}) {
  const { t } = useLocale();
  const items = getScenarioPackageItems(scenario);

  return (
    <div className="lg:hidden bg-ink text-paper rounded-xl p-4">
      <div className="text-[11px] uppercase tracking-[0.2em] text-paper/50 mb-2">
        {t("design.package")}
      </div>
      <input
        type="text"
        value={scenario.name}
        onChange={(e) => onNameChange(e.target.value)}
        className="w-full bg-paper/10 border border-paper/20 rounded px-3 py-2 text-sm mb-2 min-h-[44px]"
        aria-label="Scenario name"
      />
      <p className="text-xs text-paper/70">
        {t("design.activeInterventions", { count: items.length })} · {scenario.run.mode} mode
      </p>
    </div>
  );
}

export function ScenarioRunActions({
  scenario,
  running,
  error,
  onRun,
  className = "",
  onDark = false,
}: {
  scenario: Scenario;
  running: boolean;
  error: string | null;
  onRun: () => void;
  className?: string;
  onDark?: boolean;
}) {
  const { t } = useLocale();

  return (
    <div className={className}>
      {error && (
        <p className={`text-sm mb-2 ${onDark ? "text-red-300" : "text-negative"}`}>{error}</p>
      )}
      <button
        type="button"
        onClick={onRun}
        disabled={running}
        className="w-full min-h-[44px] py-3 bg-accent text-paper rounded-md font-medium disabled:opacity-50 hover:bg-accent/90 transition"
      >
        {running ? t("design.running") : t("design.run")}
      </button>
      {running && (
        <p className="text-xs text-paper/60 mt-2 text-center">
          {scenario.run.mode === "robust" ? t("design.runHintRobust") : t("design.runHintQuick")}
        </p>
      )}
    </div>
  );
}

export default function ScenarioSummarySidebar({
  scenario,
  running,
  error,
  onNameChange,
  onRun,
}: Props) {
  const { t } = useLocale();

  return (
    <aside className="hidden lg:block lg:sticky lg:top-24 h-fit space-y-4">
      <div className="bg-ink text-paper rounded-xl p-6">
        <div className="text-[11px] uppercase tracking-[0.2em] text-paper/50 mb-2">
          {t("design.package")}
        </div>
        <h3 className="font-display text-lg mb-4">{t("design.summary")}</h3>

        <SummaryBody scenario={scenario} onNameChange={onNameChange} />

        <div className="mt-6">
          <ScenarioRunActions
            scenario={scenario}
            running={running}
            error={error}
            onRun={onRun}
            onDark
          />
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl p-5 text-sm">
        <div className="text-[11px] uppercase tracking-wider text-ink-muted mb-2">{t("design.nextSteps")}</div>
        <p className="text-ink-soft text-xs mb-3 leading-relaxed">{t("design.nextHint")}</p>
        <Link href="/compare" className="text-xs text-accent hover:underline block mb-2">
          {t("design.startComparison")}
        </Link>
        <BackToLastComparisonLink variant="text" className="text-xs" />
      </div>
    </aside>
  );
}
