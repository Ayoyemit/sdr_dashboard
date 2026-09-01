"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useMemo, useRef } from "react";
import ResultsExportBar from "@/components/export/ResultsExportBar";
import BackToLastComparisonLink from "@/components/BackToLastComparisonLink";
import RunProgressPanel from "@/components/results/RunProgressPanel";
import GeographyScopePanel from "@/components/results/GeographyScopePanel";
import ScenarioAssumptionsBanner from "@/components/results/ScenarioAssumptionsBanner";
import ExecutiveSummary from "@/components/results/ExecutiveSummary";
import MethodsLimitations from "@/components/results/MethodsLimitations";
import BudgetLens from "@/components/results/BudgetLens";
import ResultsStories from "@/components/stories/ResultsStories";
import { useRunPoller } from "@/hooks/useRunPoller";
import { getEssentialIndicators } from "@/lib/indicators";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { buildExecutiveSummary } from "@/lib/results-summary";
import { DEFAULT_SCENARIO } from "@/lib/scenarios";
import { scenarioFromURLParams, scenarioToSearchParams } from "@/lib/url-state";

function ResultsContent() {
  const { t, locale } = useLocale();
  const searchParams = useSearchParams();
  const runId = searchParams.get("run_id");
  const exportScopeRef = useRef<HTMLDivElement>(null);
  const urlScenario = useMemo(
    () => scenarioFromURLParams(searchParams.get("s")),
    [searchParams]
  );

  const { loading, scenario, result, error, estimatedSecondsRemaining, pollCount } = useRunPoller(
    runId,
    urlScenario
  );

  const displayIndicators = useMemo(
    () => (scenario ? getEssentialIndicators(scenario) : new Set<string>()),
    [scenario]
  );

  const executiveSummary = useMemo(
    () => (result && scenario ? buildExecutiveSummary(scenario, result, t, locale) : null),
    [scenario, result, t, locale]
  );

  const designHref = useMemo(() => {
    const params = scenarioToSearchParams(scenario ?? urlScenario ?? DEFAULT_SCENARIO);
    return `/design?${params.toString()}`;
  }, [scenario, urlScenario]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-16">
        <RunProgressPanel
          scenario={scenario ?? urlScenario}
          estimatedSecondsRemaining={estimatedSecondsRemaining}
          pollCount={pollCount}
        />
      </div>
    );
  }

  if (error || !result || !scenario || !executiveSummary) {
    return (
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-16 text-center">
        <p className="text-negative mb-4">{error}</p>
        <Link href="/design" className="text-accent underline">
          {t("nav.design")}
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-8">
      <div className="mb-6 flex flex-col sm:flex-row sm:flex-wrap sm:items-start sm:justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <span className="text-[11px] tracking-[0.2em] text-accent uppercase">{t("results.step")}</span>
          </div>
          <h1 className="font-display text-2xl sm:text-3xl mb-1">{t("results.title")}</h1>
          <p className="text-ink-muted text-sm">
            {scenario.name} ·{" "}
            {t("common.yearsHorizon", {
              years: scenario.run.implementation_years + scenario.run.maintenance_years,
            })}{" "}
            · {t("common.vsBaseline")}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2 flex-wrap items-stretch sm:items-start sm:justify-end w-full sm:w-auto">
          <Link
            href="/compare"
            className="min-h-[44px] inline-flex items-center justify-center px-4 py-2 bg-ink text-paper rounded-md text-sm text-center font-medium"
          >
            {t("common.compareScenarios")}
          </Link>
          <ResultsExportBar
            mode="scenario"
            scenario={scenario}
            result={result}
            runId={runId}
            scopeRef={exportScopeRef}
          />
          <Link
            href={designHref}
            className="min-h-[44px] inline-flex items-center justify-center px-4 py-2 border border-border rounded-md text-sm hover:bg-paper-deep"
          >
            {t("common.adjustScenario")}
          </Link>
        </div>
      </div>

      <ScenarioAssumptionsBanner scenario={scenario} />

      <GeographyScopePanel scenario={scenario} />

      <ExecutiveSummary summary={executiveSummary} result={result} />

      <BudgetLens mode="single" label={scenario.name} costUsd={result.summary.cumulative_cost_usd} />

      <MethodsLimitations scenario={scenario} result={result} runId={runId} />

      <div ref={exportScopeRef}>
        <ResultsStories
          result={result}
          selectedIndicators={displayIndicators}
          countyId={scenario.county}
        />
      </div>

      <div className="mt-12 flex flex-col sm:flex-row gap-3 sm:gap-4 flex-wrap items-stretch sm:items-center">
        <Link
          href="/compare"
          className="min-h-[44px] inline-flex items-center justify-center px-6 py-3 bg-ink text-paper rounded-md text-center font-medium"
        >
          {t("common.compareScenarios")} →
        </Link>
        <Link
          href={designHref}
          className="min-h-[44px] inline-flex items-center justify-center px-6 py-3 border border-border rounded-md hover:bg-paper-deep text-center"
        >
          ← {t("common.adjustScenario")}
        </Link>
        <BackToLastComparisonLink variant="text" />
      </div>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<div className="p-8">Loading…</div>}>
      <ResultsContent />
    </Suspense>
  );
}
