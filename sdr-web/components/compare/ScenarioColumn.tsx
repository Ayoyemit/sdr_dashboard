"use client";

import { useState } from "react";
import InterventionCard from "@/components/compare/InterventionCard";
import MobileSectionTabs from "@/components/responsive/MobileSectionTabs";
import {
  getLibraryItem,
  getMomishLevel,
  getSingleLevel,
  listActiveInterventions,
  removeIntervention,
  setHssIntensity,
  setMomishLevel,
  setSingleLevel,
} from "@/lib/interventions";
import { HSSIntensity, Scenario } from "@/lib/scenarios";
import { MomishLevel, SingleInterventionLevel } from "@/lib/intervention-config";

type ColumnAccent = "a" | "b";

const ACCENT: Record<
  ColumnAccent,
  { border: string; headerBg: string; headerText: string }
> = {
  a: {
    border: "#C0D5E8",
    headerBg: "#E0EBF5",
    headerText: "#2563A8",
  },
  b: {
    border: "#BFDEC4",
    headerBg: "#DCEEE0",
    headerText: "#2B7A3E",
  },
};

interface Props {
  accent: ColumnAccent;
  scenario: Scenario;
  onChange: (scenario: Scenario) => void;
}

function ColumnInner({ accent, scenario, onChange }: Props) {
  const colors = ACCENT[accent];
  const activeIds = listActiveInterventions(scenario);

  return (
    <div
      className="rounded-xl border-2"
      style={{ borderColor: colors.border, background: accent === "a" ? "#F4F8FC" : "#F2FAF4" }}
    >
      <div
        className="px-4 sm:px-5 py-4 border-b"
        style={{ borderColor: colors.border, background: colors.headerBg }}
      >
        <input
          type="text"
          value={scenario.name}
          onChange={(e) => onChange({ ...scenario, name: e.target.value })}
          className="font-display text-base sm:text-lg bg-transparent border-none outline-none w-full min-h-[44px]"
          style={{ color: colors.headerText }}
        />
        <span className="text-[10px] text-ink-muted italic">Click name to edit</span>
      </div>

      <div className="p-3 sm:p-4 space-y-3 min-h-[160px] sm:min-h-[200px]">
        {activeIds.length === 0 ? (
          <p className="text-sm text-ink-muted text-center py-8">
            No interventions yet — add from the library using + {accent === "a" ? "A" : "B"}
          </p>
        ) : (
          activeIds.map((id) => {
            const item = getLibraryItem(id);
            return (
              <InterventionCard
                key={id}
                id={id}
                hssIntensity={scenario.hss.intensity}
                singleLevel={
                  item.group === "single"
                    ? (getSingleLevel(scenario, id) as SingleInterventionLevel)
                    : undefined
                }
                momishLevel={
                  item.group === "momish" ? getMomishLevel(scenario, id) : undefined
                }
                onHssChange={
                  id === "hss"
                    ? (intensity: HSSIntensity) => onChange(setHssIntensity(scenario, intensity))
                    : undefined
                }
                onSingleChange={
                  item.group === "single"
                    ? (level) => onChange(setSingleLevel(scenario, id, level))
                    : undefined
                }
                onMomishChange={
                  item.group === "momish"
                    ? (level: MomishLevel) => onChange(setMomishLevel(scenario, id, level))
                    : undefined
                }
                onRemove={() => onChange(removeIntervention(scenario, id))}
              />
            );
          })
        )}
      </div>
    </div>
  );
}

interface CompareColumnsProps {
  scenarioA: Scenario;
  scenarioB: Scenario;
  onChangeA: (scenario: Scenario) => void;
  onChangeB: (scenario: Scenario) => void;
}

export function CompareScenarioColumns({
  scenarioA,
  scenarioB,
  onChangeA,
  onChangeB,
}: CompareColumnsProps) {
  const [activeTab, setActiveTab] = useState("a");

  return (
    <>
      <MobileSectionTabs
        tabs={[
          { id: "a", label: scenarioA.name.split("·")[0]?.trim() || "Scenario A" },
          { id: "b", label: scenarioB.name.split("·")[0]?.trim() || "Scenario B" },
        ]}
        activeId={activeTab}
        onChange={setActiveTab}
        accent={activeTab === "a" ? "a" : "b"}
      />

      <div className="md:hidden mt-4">
        {activeTab === "a" ? (
          <ColumnInner accent="a" scenario={scenarioA} onChange={onChangeA} />
        ) : (
          <ColumnInner accent="b" scenario={scenarioB} onChange={onChangeB} />
        )}
      </div>

      <div className="hidden md:grid md:grid-cols-2 gap-5">
        <ColumnInner accent="a" scenario={scenarioA} onChange={onChangeA} />
        <ColumnInner accent="b" scenario={scenarioB} onChange={onChangeB} />
      </div>
    </>
  );
}

export default function ScenarioColumn({ accent, scenario, onChange }: Props) {
  return <ColumnInner accent={accent} scenario={scenario} onChange={onChange} />;
}
