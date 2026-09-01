import { Scenario } from "./scenarios";
import { getLibraryItem, getMomishLevel, getSingleLevel } from "./intervention-config";

export interface ScenarioPackageItem {
  label: string;
  detail?: string;
  wired: boolean;
}

const SINGLE_KEYS = [
  "pph_bundle",
  "iv_iron",
  "mgso4",
  "antibiotics",
  "oxytocin",
  "ultrasound",
  "intrapartum_sensors",
] as const;

const MOMISH_KEYS = [
  "prompts",
  "mentors",
  "fqa",
  "pulse",
  "referral_emt",
  "blood_tracking",
] as const;

export function getScenarioPackageItems(scenario: Scenario): ScenarioPackageItem[] {
  const items: ScenarioPackageItem[] = [];

  for (const id of MOMISH_KEYS) {
    const level = getMomishLevel(scenario, id);
    if (level !== "off") {
      items.push({
        label: getLibraryItem(id).name,
        detail: level,
        wired: getLibraryItem(id).wired === "wired",
      });
    }
  }

  for (const id of SINGLE_KEYS) {
    const level = getSingleLevel(scenario, id);
    if (level !== "off") {
      items.push({
        label: getLibraryItem(id).name,
        detail: level === "on" ? "on" : level,
        wired: getLibraryItem(id).wired === "wired",
      });
    }
  }

  if (scenario.hss.enabled && scenario.hss.intensity !== "off") {
    items.push({
      label: "Health System Strengthening",
      detail: scenario.hss.intensity,
      wired: true,
    });
  }

  if (items.length === 0) {
    items.push({ label: "Baseline only", detail: "no intervention", wired: true });
  }

  return items;
}

export function getScenarioHorizonYears(scenario: Scenario): number {
  return scenario.run.implementation_years + scenario.run.maintenance_years;
}
