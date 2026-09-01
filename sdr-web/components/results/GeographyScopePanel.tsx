"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import GeographyPicker from "@/components/geography/GeographyPicker";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { countyDisplayName, formatCountyPopulation, getCountyById } from "@/lib/counties";
import { listActiveInterventions, INTERVENTION_LIBRARY } from "@/lib/interventions";
import {
  resultsHrefForRun,
  scenarioForCounty,
  startRunForGeography,
} from "@/lib/geography-run";
import { Scenario, SupportedCountyId } from "@/lib/scenarios";

interface Props {
  scenario: Scenario;
}

export default function GeographyScopePanel({ scenario }: Props) {
  const { t } = useLocale();
  const router = useRouter();
  const [runningCounty, setRunningCounty] = useState<SupportedCountyId | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cacheHint, setCacheHint] = useState(false);

  const meta = getCountyById(scenario.county);
  const population = formatCountyPopulation(meta?.population);
  const county = countyDisplayName(scenario.county);
  const activeLabels = listActiveInterventions(scenario)
    .map((id) => INTERVENTION_LIBRARY.find((item) => item.id === id)?.name ?? id)
    .join(" · ");

  const handleRerun = async (countyId: SupportedCountyId) => {
    if (countyId === scenario.county || runningCounty) return;
    setRunningCounty(countyId);
    setError(null);
    setCacheHint(false);
    const nextScenario = scenarioForCounty(scenario, countyId);
    try {
      const { runId, fromCache } = await startRunForGeography(nextScenario);
      setCacheHint(fromCache);
      router.push(resultsHrefForRun(nextScenario, runId));
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : t("geography.runFailed", { county: countyDisplayName(countyId) })
      );
      setRunningCounty(null);
    }
  };

  return (
    <div className="mb-6 rounded-xl border border-border bg-paper-deep/60 overflow-hidden">
      <div className="px-4 py-3 border-b border-border/80 bg-card/50">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <strong className="text-xs uppercase tracking-wider text-ink">
            {t("geography.title")}
          </strong>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-accent/10 text-accent font-medium">
            {t("geography.resultsFor", { county })}
          </span>
        </div>
        <p className="text-sm text-ink-soft leading-relaxed">
          {t("scope.body", { county, population })}
        </p>
      </div>

      <div className="px-4 py-4 space-y-3">
        <div>
          <p className="text-xs font-medium text-ink mb-2">{t("geography.runSamePackage")}</p>
          <p className="text-[11px] text-ink-muted mb-3 leading-relaxed">
            {t("geography.resultsHint")}
          </p>
          {activeLabels && (
            <p className="text-[11px] text-ink-soft mb-3 leading-relaxed border-l-2 border-accent/40 pl-3">
              <span className="font-medium text-ink">{t("geography.packageLabel")}: </span>
              {activeLabels}
            </p>
          )}
          <GeographyPicker
            value={scenario.county}
            mode="rerun"
            runningCountyId={runningCounty}
            onChange={handleRerun}
          />
        </div>

        {runningCounty && (
          <p className="text-sm text-ink-muted" role="status">
            {t("geography.running", { county: countyDisplayName(runningCounty) })}
          </p>
        )}
        {cacheHint && !runningCounty && (
          <p className="text-xs text-intervention">{t("geography.cacheHit")}</p>
        )}
        {error && (
          <p className="text-sm text-negative" role="alert">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
