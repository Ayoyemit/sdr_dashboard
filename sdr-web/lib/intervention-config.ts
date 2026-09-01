import { HSSIntensity, Scenario } from "./scenarios";

export type InterventionGroup = "momish" | "single" | "hss";

export type InterventionId =
  | "hss"
  | "pph_bundle"
  | "iv_iron"
  | "mgso4"
  | "antibiotics"
  | "oxytocin"
  | "ultrasound"
  | "intrapartum_sensors"
  | "prompts"
  | "mentors"
  | "fqa"
  | "pulse"
  | "referral_emt"
  | "blood_tracking";

export type SingleInterventionLevel = "off" | "current" | "improved" | "maximal";
export type MomishLevel = "off" | "current" | "moderate" | "intensive";
export type BinaryLevel = "off" | "on";

export interface LibraryItem {
  id: InterventionId;
  name: string;
  group: InterventionGroup;
  description: string;
  wired: "wired" | "ui-only" | "partial";
  /** Design page control style */
  control: "momish" | "binary" | "graded-single";
}

export const GROUP_ORDER: InterventionGroup[] = ["momish", "single", "hss"];

export const GROUP_LABEL_KEYS: Record<InterventionGroup, string> = {
  momish: "interventions.groupMomish",
  single: "interventions.groupSingle",
  hss: "interventions.groupHss",
};

export const HSS_DESIGN_OPTIONS: { value: HSSIntensity; labelKey: string; hintKey?: string }[] = [
  { value: "off", labelKey: "interventions.levelOff" },
  { value: "light", labelKey: "interventions.hssLight", hintKey: "interventions.hssLightHint" },
  { value: "moderate", labelKey: "interventions.hssModerate", hintKey: "interventions.hssModerateHint" },
  { value: "intensive", labelKey: "interventions.hssIntensive", hintKey: "interventions.hssIntensiveHint" },
];

export const HSS_COMPARE_OPTIONS: { value: HSSIntensity; labelKey: string }[] = [
  { value: "light", labelKey: "interventions.hssConservative" },
  { value: "moderate", labelKey: "interventions.hssModerate" },
  { value: "intensive", labelKey: "interventions.hssAggressive" },
];

export const SINGLE_COMPARE_OPTIONS: { value: SingleInterventionLevel; labelKey: string }[] = [
  { value: "current", labelKey: "interventions.levelCurrent" },
  { value: "improved", labelKey: "interventions.levelImproved" },
  { value: "maximal", labelKey: "interventions.levelMaximal" },
];

export const MOMISH_OPTIONS: { value: MomishLevel; labelKey: string }[] = [
  { value: "off", labelKey: "interventions.levelOff" },
  { value: "current", labelKey: "interventions.levelCurrent" },
  { value: "moderate", labelKey: "interventions.levelModerate" },
  { value: "intensive", labelKey: "interventions.levelIntensive" },
];

const LIBRARY_ITEMS: LibraryItem[] = [
  { id: "blood_tracking", name: "Blood Tracking", group: "momish", description: "Blood product tracking in facilities", wired: "wired", control: "momish" },
  { id: "fqa", name: "FQA", group: "momish", description: "Facility quality assessment", wired: "wired", control: "momish" },
  { id: "mentors", name: "MENTORS", group: "momish", description: "Mentorship sessions for providers", wired: "wired", control: "momish" },
  { id: "prompts", name: "PROMPTS", group: "momish", description: "Community engagement via PROMPTS", wired: "wired", control: "momish" },
  { id: "pulse", name: "PULSE", group: "momish", description: "Pulse oximetry monitoring program", wired: "wired", control: "momish" },
  { id: "referral_emt", name: "Referral / EMT", group: "momish", description: "Emergency medical transfer network", wired: "partial", control: "momish" },
  { id: "antibiotics", name: "Antibiotics", group: "single", description: "Antibiotics for maternal sepsis", wired: "wired", control: "binary" },
  { id: "intrapartum_sensors", name: "Intrapartum Sensors", group: "single", description: "Fetal monitoring sensors at facilities", wired: "wired", control: "graded-single" },
  { id: "iv_iron", name: "IV Iron", group: "single", description: "Intravenous iron for anaemia", wired: "wired", control: "binary" },
  { id: "mgso4", name: "MgSO4", group: "single", description: "Magnesium sulfate for eclampsia", wired: "wired", control: "binary" },
  { id: "oxytocin", name: "Oxytocin", group: "single", description: "Oxytocin for prolonged labour", wired: "wired", control: "binary" },
  { id: "ultrasound", name: "POCUS (point-of-care ultrasound)", group: "single", description: "Portable point-of-care ultrasound", wired: "wired", control: "graded-single" },
  { id: "pph_bundle", name: "PPH Bundle", group: "single", description: "Postpartum haemorrhage treatment bundle", wired: "wired", control: "binary" },
  { id: "hss", name: "Health System Strengthening", group: "hss", description: "Facility capacity, training, and supply chain", wired: "wired", control: "momish" },
];

export function getInterventionLibrary(): LibraryItem[] {
  return GROUP_ORDER.flatMap((group) =>
    LIBRARY_ITEMS.filter((item) => item.group === group).sort((a, b) =>
      a.name.localeCompare(b.name)
    )
  );
}

export function getLibraryItem(id: InterventionId): LibraryItem {
  return LIBRARY_ITEMS.find((item) => item.id === id)!;
}

function getUiLevel(scenario: Scenario, id: InterventionId): string | undefined {
  return scenario.ui_levels?.[id];
}

function setUiLevel(scenario: Scenario, id: InterventionId, level: string | undefined): Scenario {
  const ui_levels = { ...(scenario.ui_levels ?? {}) };
  if (!level || level === "off") {
    delete ui_levels[id];
  } else {
    ui_levels[id] = level;
  }
  return { ...scenario, ui_levels };
}

const MOMISH_ADOPTION: Record<MomishLevel, number> = {
  off: 0,
  current: 0.35,
  moderate: 0.65,
  intensive: 0.9,
};

function momishFidelity(level: MomishLevel): "low" | "high" {
  return level === "intensive" ? "high" : "low";
}

export function getMomishLevel(scenario: Scenario, id: InterventionId): MomishLevel {
  const stored = getUiLevel(scenario, id) as MomishLevel | undefined;
  if (stored) return stored;

  switch (id) {
    case "prompts":
      return scenario.community.prompts.enabled ? "moderate" : "off";
    case "mentors":
      return scenario.community.mentors.enabled ? "moderate" : "off";
    case "fqa":
      return scenario.community.fqa.enabled
        ? scenario.community.fqa.implementation === "high"
          ? "intensive"
          : "current"
        : "off";
    case "pulse":
      return scenario.community.pulse.enabled
        ? scenario.community.pulse.implementation === "high"
          ? "intensive"
          : "current"
        : "off";
    case "referral_emt":
      return scenario.community.referral_emt.enabled ? "moderate" : "off";
    case "blood_tracking":
      return scenario.community.blood_tracking?.enabled
        ? (scenario.community.blood_tracking.level as MomishLevel) ?? "current"
        : "off";
    default:
      return "off";
  }
}

export function setMomishLevel(
  scenario: Scenario,
  id: InterventionId,
  level: MomishLevel
): Scenario {
  let next = setUiLevel(scenario, id, level === "off" ? undefined : level);
  const adoption = MOMISH_ADOPTION[level];

  switch (id) {
    case "prompts":
      next = {
        ...next,
        community: {
          ...next.community,
          enabled: level !== "off",
          prompts: {
            enabled: level !== "off",
            adoption,
            chv_engagement: adoption,
            intervention_fidelity: level === "intensive" ? 0.87 : level === "moderate" ? 0.75 : 0.6,
          },
        },
      };
      break;
    case "mentors":
      next = {
        ...next,
        community: {
          ...next.community,
          enabled: level !== "off" || next.community.prompts.enabled,
          mentors: {
            enabled: level !== "off",
            adoption,
            attendance: adoption,
            fidelity: level === "intensive" ? 0.87 : 0.75,
          },
        },
      };
      break;
    case "fqa":
      next = {
        ...next,
        community: {
          ...next.community,
          enabled: level !== "off" || next.community.prompts.enabled || next.community.mentors.enabled,
          fqa: {
            enabled: level !== "off",
            implementation: momishFidelity(level),
            influence_on_pulse: level === "intensive" ? "high" : "low",
          },
        },
      };
      break;
    case "pulse":
      next = {
        ...next,
        community: {
          ...next.community,
          enabled: level !== "off" || next.community.prompts.enabled || next.community.mentors.enabled,
          pulse: { enabled: level !== "off", implementation: momishFidelity(level) },
        },
      };
      break;
    case "referral_emt":
      next = {
        ...next,
        community: {
          ...next.community,
          enabled: level !== "off" || next.community.prompts.enabled || next.community.mentors.enabled,
          referral_emt: {
            enabled: level !== "off",
            emt_participation: adoption,
          },
        },
      };
      break;
    case "blood_tracking":
      next = {
        ...next,
        community: {
          ...next.community,
          enabled:
            level !== "off" ||
            next.community.prompts.enabled ||
            next.community.mentors.enabled ||
            next.community.fqa.enabled ||
            next.community.pulse.enabled ||
            next.community.referral_emt.enabled,
          blood_tracking: {
            enabled: level !== "off",
            level:
              level === "intensive" || level === "moderate" || level === "current"
                ? level
                : "current",
          },
        },
      };
      break;
  }

  return next;
}

function treatmentsHasActive(treatments: Scenario["treatments"]): boolean {
  return !!(
    treatments.pph_bundle ||
    treatments.iv_iron ||
    treatments.mgso4 ||
    treatments.antibiotics ||
    treatments.oxytocin ||
    treatments.ultrasound ||
    treatments.intrapartum_sensors
  );
}

export function getSingleLevel(
  scenario: Scenario,
  id: InterventionId
): SingleInterventionLevel | BinaryLevel {
  const stored = getUiLevel(scenario, id);
  if (stored) return stored as SingleInterventionLevel;

  if (id === "intrapartum_sensors") {
    if (!scenario.treatments.intrapartum_sensors) return "off";
    if (scenario.treatments.intrapartum_sensors_ai) return "improved";
    return "current";
  }

  const item = getLibraryItem(id);
  const on = hasInterventionActive(scenario, id);
  if (!on) return "off";
  return item.control === "binary" ? "on" : "current";
}

export function setSingleLevel(
  scenario: Scenario,
  id: InterventionId,
  level: SingleInterventionLevel | BinaryLevel
): Scenario {
  const isOn = level !== "off";
  let next = setUiLevel(scenario, id, level === "off" ? undefined : level);

  switch (id) {
    case "pph_bundle":
    case "iv_iron":
    case "mgso4":
    case "antibiotics":
    case "oxytocin":
    case "ultrasound": {
      const treatments = { ...next.treatments, [id]: isOn };
      next = { ...next, treatments: { ...treatments, enabled: treatmentsHasActive(treatments) } };
      break;
    }
    case "intrapartum_sensors": {
      const sensorsOn = level !== "off";
      const aiOn = level === "improved" || level === "maximal";
      const treatments = {
        ...next.treatments,
        intrapartum_sensors: sensorsOn,
        intrapartum_sensors_ai: aiOn,
      };
      next = { ...next, treatments: { ...treatments, enabled: treatmentsHasActive(treatments) } };
      break;
    }
  }

  return next;
}

export function hasInterventionActive(scenario: Scenario, id: InterventionId): boolean {
  switch (id) {
    case "hss":
      return scenario.hss.enabled && scenario.hss.intensity !== "off";
    case "pph_bundle":
    case "iv_iron":
    case "mgso4":
    case "antibiotics":
    case "oxytocin":
    case "ultrasound":
      return !!scenario.treatments[id];
    case "intrapartum_sensors":
      return !!scenario.treatments.intrapartum_sensors;
    case "prompts":
    case "mentors":
    case "fqa":
    case "pulse":
    case "referral_emt":
      return getMomishLevel(scenario, id) !== "off";
    case "blood_tracking":
      return getMomishLevel(scenario, id) !== "off";
    default:
      return false;
  }
}

export function listActiveInterventions(scenario: Scenario): InterventionId[] {
  return getInterventionLibrary()
    .map((item) => item.id)
    .filter((id) => hasInterventionActive(scenario, id));
}

export function applyIntervention(
  scenario: Scenario,
  id: InterventionId,
  opts?: { hssIntensity?: HSSIntensity }
): Scenario {
  if (id === "hss") {
    const intensity = opts?.hssIntensity ?? (scenario.hss.intensity === "off" ? "moderate" : scenario.hss.intensity);
    return {
      ...scenario,
      hss: { ...scenario.hss, enabled: true, intensity },
    };
  }
  const item = getLibraryItem(id);
  if (item.group === "momish") {
    return setMomishLevel(scenario, id, "moderate");
  }
  if (item.control === "binary") {
    return setSingleLevel(scenario, id, "on");
  }
  return setSingleLevel(scenario, id, "current");
}

export function removeIntervention(scenario: Scenario, id: InterventionId): Scenario {
  if (id === "hss") {
    return { ...scenario, hss: { ...scenario.hss, enabled: false, intensity: "off" } };
  }
  if (getLibraryItem(id).group === "momish" || id === "blood_tracking") {
    return setMomishLevel(scenario, id, "off");
  }
  return setSingleLevel(scenario, id, "off");
}

export function setHssIntensity(scenario: Scenario, intensity: HSSIntensity): Scenario {
  return {
    ...scenario,
    hss: {
      ...scenario.hss,
      enabled: intensity !== "off",
      intensity,
    },
  };
}

export function hssCoverageHint(intensity: HSSIntensity): string | undefined {
  switch (intensity) {
    case "light":
      return "60–69%";
    case "moderate":
      return "70–79%";
    case "intensive":
      return "80–95%";
    default:
      return undefined;
  }
}
