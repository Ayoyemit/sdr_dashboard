"use client";

import PillSelector from "@/components/PillSelector";
import { useLocale } from "@/components/i18n/LocaleProvider";
import {
  getInterventionLibrary,
  getMomishLevel,
  getSingleLevel,
  HSS_DESIGN_OPTIONS,
  MOMISH_OPTIONS,
  setHssIntensity,
  setMomishLevel,
  setSingleLevel,
  hssCoverageHint,
} from "@/lib/interventions";
import { HSSIntensity, Scenario } from "@/lib/scenarios";

interface Props {
  scenario: Scenario;
  onChange: (scenario: Scenario) => void;
}

function gradedSingleOptions(t: (k: string) => string) {
  return [
    { value: "off", label: t("interventions.levelOff") },
    { value: "current", label: t("interventions.levelCurrent") },
    { value: "improved", label: t("interventions.levelImproved") },
  ];
}

function binaryOptions(t: (k: string) => string) {
  return [
    { value: "off", label: t("interventions.levelOff") },
    { value: "on", label: t("interventions.levelOn") },
  ];
}

export default function DesignInterventionPillars({ scenario, onChange }: Props) {
  const { t } = useLocale();
  const library = getInterventionLibrary();

  const momishItems = library.filter((i) => i.group === "momish");
  const singleItems = library.filter((i) => i.group === "single");

  const hssOptions = HSS_DESIGN_OPTIONS.map((o) => ({
    value: o.value,
    label: t(o.labelKey),
    hint: o.hintKey ? t(o.hintKey) : undefined,
  }));

  const momishOpts = MOMISH_OPTIONS.map((o) => ({
    value: o.value,
    label: t(o.labelKey),
  }));

  return (
    <div className="space-y-6">
      <section className="bg-card border border-border rounded-xl p-4 md:p-6">
        <h2 className="font-display text-lg mb-4">{t("design.pillar1")}</h2>
        <div className="space-y-5">
          {momishItems.map((item) => (
            <div key={item.id}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium">{item.name}</span>
                {item.wired === "ui-only" && (
                  <span className="text-[10px] text-warning">● {t("common.uiOnly")}</span>
                )}
              </div>
              <PillSelector
                options={momishOpts}
                value={getMomishLevel(scenario, item.id)}
                onChange={(v) => onChange(setMomishLevel(scenario, item.id, v as "off" | "current" | "moderate" | "intensive"))}
              />
            </div>
          ))}
        </div>
      </section>

      <section className="bg-card border border-border rounded-xl p-4 md:p-6">
        <h2 className="font-display text-lg mb-4">{t("design.pillar2")}</h2>
        <div className="space-y-5">
          {singleItems.map((item) => {
            const options =
              item.control === "graded-single"
                ? gradedSingleOptions(t)
                : binaryOptions(t);
            const value = getSingleLevel(scenario, item.id);
            return (
              <div key={item.id}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium">{item.name}</span>
                  {item.wired === "ui-only" && (
                    <span className="text-[10px] text-warning">● {t("common.uiOnly")}</span>
                  )}
                </div>
                <PillSelector
                  options={options}
                  value={value}
                  onChange={(v) =>
                    onChange(
                      setSingleLevel(
                        scenario,
                        item.id,
                        v as "off" | "on" | "current" | "improved" | "maximal"
                      )
                    )
                  }
                />
              </div>
            );
          })}
        </div>
      </section>

      <section className="bg-card border border-border rounded-xl p-4 md:p-6">
        <h2 className="font-display text-lg mb-4">{t("design.pillar3")}</h2>
        <PillSelector
          options={hssOptions}
          value={scenario.hss.intensity}
          onChange={(v) => onChange(setHssIntensity(scenario, v as HSSIntensity))}
        />
        {scenario.hss.intensity !== "off" && hssCoverageHint(scenario.hss.intensity) && (
          <p className="text-xs text-ink-muted mt-3">
            {t("interventions.coverageRange", {
              range: hssCoverageHint(scenario.hss.intensity)!,
            })}
          </p>
        )}
      </section>
    </div>
  );
}
