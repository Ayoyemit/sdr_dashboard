"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import BackToLastResultsLink from "@/components/BackToLastResultsLink";
import BackToLastComparisonLink from "@/components/BackToLastComparisonLink";
import InterventionLibrary, {
  applyIntervention,
} from "@/components/compare/InterventionLibrary";
import { CompareScenarioColumns } from "@/components/compare/ScenarioColumn";
import StickyActionBar from "@/components/responsive/StickyActionBar";
import { compareScenarios } from "@/lib/api";
import {
  hasIntervention,
  mergeScenario,
  QUICK_COMPARE_PRESETS,
  removeIntervention,
  InterventionId,
} from "@/lib/interventions";
import { DEFAULT_SCENARIO, Scenario } from "@/lib/scenarios";
import { scenarioFromURLParams } from "@/lib/url-state";
import { getLastRun } from "@/lib/last-run-storage";

import { getLastCompareResultsHref, saveLastComparison } from "@/lib/compare-storage";

export default function ComparePage() {
  const router = useRouter();
  const [scenarioA, setScenarioA] = useState<Scenario>({
    ...DEFAULT_SCENARIO,
    name: "Scenario A · Baseline",
    hss: { enabled: true, intensity: "moderate" },
  });
  const [scenarioB, setScenarioB] = useState<Scenario>({
    ...DEFAULT_SCENARIO,
    name: "Scenario B · Intensive + Treatments",
    hss: { enabled: true, intensity: "intensive" },
    treatments: { enabled: true, pph_bundle: true, mgso4: true },
    community: {
      enabled: true,
      prompts: { enabled: true, adoption: 0.7, chv_engagement: 0.7 },
      mentors: { enabled: false },
      fqa: { enabled: false, implementation: "low", influence_on_pulse: "low" },
      pulse: { enabled: false, implementation: "low" },
      referral_emt: { enabled: false },
    },
  });
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const last = getLastRun();
    if (!last) return;
    const fromLastRun = scenarioFromURLParams(last.scenarioEncoded);
    if (fromLastRun) {
      setScenarioA({
        ...fromLastRun,
        name: fromLastRun.name || "Scenario A · Your run",
      });
    }
  }, []);

  const handleLibraryAdd = useCallback(
    (target: "a" | "b", id: InterventionId) => {
      const setter = target === "a" ? setScenarioA : setScenarioB;
      const current = target === "a" ? scenarioA : scenarioB;
      setter(
        hasIntervention(current, id)
          ? removeIntervention(current, id)
          : applyIntervention(current, id)
      );
    },
    [scenarioA, scenarioB]
  );

  const applyQuickPreset = (index: number) => {
    const preset = QUICK_COMPARE_PRESETS[index];
    setScenarioA(mergeScenario(DEFAULT_SCENARIO, { name: "Scenario A", ...preset.a }));
    setScenarioB(mergeScenario(DEFAULT_SCENARIO, { name: "Scenario B", ...preset.b }));
  };

  const handleCompare = async () => {
    setRunning(true);
    setError(null);
    try {
      const response = await compareScenarios(scenarioA, scenarioB, scenarioA.run.mode);
      saveLastComparison(response);
      const params = new URLSearchParams();
      params.set("comparison_id", response.comparison_id);
      router.push(`/compare/results?${params.toString()}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Comparison failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 md:py-8 pb-24 lg:pb-8">
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-3 order-2 lg:order-1">
          <InterventionLibrary
            scenarioA={scenarioA}
            scenarioB={scenarioB}
            onAdd={handleLibraryAdd}
          />
        </div>

        <main className="col-span-12 lg:col-span-9 order-1 lg:order-2">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-6 gap-4">
            <div>
              <div className="text-[11px] tracking-[0.2em] text-accent uppercase mb-3">
                Design scenarios
              </div>
              <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-light leading-tight">
                Scenario Comparison
              </h1>
              <p className="text-ink-soft mt-3 max-w-xl text-sm sm:text-base">
                Build intervention scenarios across all three pillars and compare projected
                outcomes.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <BackToLastComparisonLink />
              <BackToLastResultsLink />
            </div>
          </div>

          <div className="mb-7 -mx-4 px-4 overflow-x-auto scrollbar-none">
            <div className="flex items-center gap-2 min-w-max pb-1">
              <span className="text-xs text-ink-muted shrink-0">Quick start:</span>
              {QUICK_COMPARE_PRESETS.map((p, i) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => applyQuickPreset(i)}
                  className="min-h-[44px] px-3 py-1.5 border border-border rounded-full text-xs hover:bg-paper-deep whitespace-nowrap"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div className="mb-8">
            <CompareScenarioColumns
              scenarioA={scenarioA}
              scenarioB={scenarioB}
              onChangeA={setScenarioA}
              onChangeB={setScenarioB}
            />
          </div>

          <div className="flex items-center gap-4 flex-wrap hidden lg:flex">
            <label className="text-sm text-ink-muted flex items-center gap-2">
              Run mode:
              <select
                value={scenarioA.run.mode}
                onChange={(e) => {
                  const mode = e.target.value as "quick" | "robust";
                  setScenarioA({ ...scenarioA, run: { ...scenarioA.run, mode } });
                  setScenarioB({ ...scenarioB, run: { ...scenarioB.run, mode } });
                }}
                className="border border-border rounded px-2 py-1 text-sm min-h-[44px]"
              >
                <option value="quick">Quick</option>
                <option value="robust">Robust</option>
              </select>
            </label>
          </div>

          {error && <p className="text-negative mt-4 hidden lg:block">{error}</p>}

          <button
            type="button"
            onClick={handleCompare}
            disabled={running}
            className="mt-8 px-8 py-3 bg-accent text-paper rounded-md font-medium disabled:opacity-50 hover:bg-accent/90 transition hidden lg:inline-flex min-h-[44px] items-center"
          >
            {running ? "Running comparison…" : "Run comparison →"}
          </button>
        </main>
      </div>

      <StickyActionBar>
        <div className="flex flex-col gap-2">
          <label className="text-sm text-ink-muted flex items-center gap-2 lg:hidden">
            Run mode:
            <select
              value={scenarioA.run.mode}
              onChange={(e) => {
                const mode = e.target.value as "quick" | "robust";
                setScenarioA({ ...scenarioA, run: { ...scenarioA.run, mode } });
                setScenarioB({ ...scenarioB, run: { ...scenarioB.run, mode } });
              }}
              className="flex-1 border border-border rounded px-2 py-2 text-sm min-h-[44px]"
            >
              <option value="quick">Quick</option>
              <option value="robust">Robust</option>
            </select>
          </label>
          {error && <p className="text-negative text-sm">{error}</p>}
          <button
            type="button"
            onClick={handleCompare}
            disabled={running}
            className="w-full min-h-[44px] py-3 bg-accent text-paper rounded-md font-medium disabled:opacity-50 hover:bg-accent/90 transition"
          >
            {running ? "Running comparison…" : "Run comparison →"}
          </button>
        </div>
      </StickyActionBar>
    </div>
  );
}
