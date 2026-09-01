"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import DesignInterventionPillars from "@/components/design/DesignInterventionPillars";
import ScenarioSummarySidebar, {
  ScenarioRunActions,
  ScenarioSummaryCompact,
} from "@/components/design/ScenarioSummarySidebar";
import GeographyPicker from "@/components/geography/GeographyPicker";
import StickyActionBar from "@/components/responsive/StickyActionBar";
import { useCounty } from "@/components/county/CountyProvider";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { resultsHrefForRun, startRunForGeography } from "@/lib/geography-run";
import { clearLastComparisonSession } from "@/lib/compare-storage";
import { DEFAULT_SCENARIO, Scenario, SupportedCountyId } from "@/lib/scenarios";
import { scenarioFromURLParams } from "@/lib/url-state";

function DesignContent() {
  const { t } = useLocale();
  const { countyId, setCountyId } = useCounty();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [scenario, setScenario] = useState<Scenario>(DEFAULT_SCENARIO);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fromUrl = scenarioFromURLParams(searchParams.get("s"));
    if (fromUrl) {
      setScenario(fromUrl);
      setCountyId(fromUrl.county);
    }
  }, [searchParams, setCountyId]);

  useEffect(() => {
    if (!searchParams.get("s")) {
      setScenario((prev) => ({ ...prev, county: countyId }));
    }
  }, [countyId, searchParams]);

  const handleGeographyChange = useCallback(
    (id: SupportedCountyId) => {
      setCountyId(id);
      setScenario((prev) => ({ ...prev, county: id }));
    },
    [setCountyId]
  );

  const update = useCallback((patch: Partial<Scenario>) => {
    setScenario((prev) => ({ ...prev, ...patch }));
  }, []);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      clearLastComparisonSession();
      const payload = { ...scenario, county: scenario.county };
      const { runId } = await startRunForGeography(payload);
      router.push(resultsHrefForRun(payload, runId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunning(false);
    }
  };

  const totalYears = scenario.run.implementation_years + scenario.run.maintenance_years;

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 md:py-8 pb-24 lg:pb-8">
      <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h1 className="font-display text-2xl sm:text-3xl mb-2">{t("design.title")}</h1>
            <p className="text-ink-muted text-sm">{t("design.subtitle")}</p>
          </div>

          <section className="bg-card border border-border rounded-xl p-4 md:p-6">
            <h2 className="font-display text-lg mb-1">{t("geography.title")}</h2>
            <p className="text-sm text-ink-muted mb-4 leading-relaxed">{t("geography.designHint")}</p>
            <GeographyPicker value={scenario.county} onChange={handleGeographyChange} />
          </section>

          <ScenarioSummaryCompact scenario={scenario} onNameChange={(name) => update({ name })} />

          <DesignInterventionPillars
            scenario={scenario}
            onChange={(next) => setScenario(next)}
          />

          <section id="run-settings" className="bg-card border border-border rounded-xl p-4 md:p-6 scroll-mt-24">
            <h2 className="font-display text-lg mb-4">{t("design.runSettings")}</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-ink-muted block mb-2">
                  {t("design.timeline", {
                    years: totalYears,
                    impl: scenario.run.implementation_years,
                    maint: scenario.run.maintenance_years,
                  })}
                </label>
                <input
                  type="range"
                  min={1}
                  max={6}
                  value={scenario.run.implementation_years}
                  onChange={(e) =>
                    update({
                      run: { ...scenario.run, implementation_years: Number(e.target.value) },
                    })
                  }
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-sm text-ink-muted block mb-2">{t("design.runMode")}</label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { value: "quick", label: "Quick", hint: "1 min" },
                    { value: "robust", label: "Robust", hint: "Multiple runs + CI" },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() =>
                        update({ run: { ...scenario.run, mode: opt.value as "quick" | "robust" } })
                      }
                      className={`pill min-h-[44px] px-4 py-2 rounded-full border border-border text-sm ${
                        scenario.run.mode === opt.value ? "active" : "bg-card hover:bg-paper-deep"
                      }`}
                    >
                      {opt.label}
                      <span className="block text-[10px] opacity-70 mt-0.5">{opt.hint}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>

        <ScenarioSummarySidebar
          scenario={scenario}
          running={running}
          error={error}
          onNameChange={(name) => update({ name })}
          onRun={handleRun}
        />
      </div>

      <StickyActionBar>
        <ScenarioRunActions
          scenario={scenario}
          running={running}
          error={error}
          onRun={handleRun}
        />
      </StickyActionBar>
    </div>
  );
}

export default function DesignPage() {
  return (
    <Suspense fallback={<div className="p-8 text-ink-muted">Loading…</div>}>
      <DesignContent />
    </Suspense>
  );
}
