import { HSSIntensity, Scenario } from "./scenarios";
import { DEFAULT_SCENARIO } from "./scenarios";
import { getInterventionLibrary } from "./intervention-config";

export {
  applyIntervention,
  getInterventionLibrary,
  getLibraryItem,
  getMomishLevel,
  getSingleLevel,
  GROUP_LABEL_KEYS,
  GROUP_ORDER,
  hasInterventionActive as hasIntervention,
  HSS_COMPARE_OPTIONS,
  HSS_DESIGN_OPTIONS,
  listActiveInterventions,
  MOMISH_OPTIONS,
  removeIntervention,
  setHssIntensity,
  setMomishLevel,
  setSingleLevel,
  SINGLE_COMPARE_OPTIONS,
  hssCoverageHint,
  type BinaryLevel,
  type InterventionGroup,
  type InterventionId,
  type LibraryItem,
  type MomishLevel,
  type SingleInterventionLevel,
} from "./intervention-config";

/** @deprecated Use getInterventionLibrary() */
export const INTERVENTION_LIBRARY = getInterventionLibrary();

/** @deprecated Use GROUP_LABEL_KEYS */
export const GROUP_LABELS: Record<string, { label: string; dot: string }> = {
  momish: { label: "System Interventions (MOMISH)", dot: "bg-accent" },
  single: { label: "Single Interventions", dot: "bg-warning" },
  hss: { label: "Health System Strengthening (HSS)", dot: "bg-intervention" },
};

export const QUICK_COMPARE_PRESETS: {
  label: string;
  a: Partial<Scenario>;
  b: Partial<Scenario>;
}[] = [
  {
    label: "Baseline vs HSS Aggressive",
    a: { name: "Scenario A · Status quo", hss: { enabled: false, intensity: "off" } },
    b: { name: "Scenario B · HSS Aggressive", hss: { enabled: true, intensity: "intensive" } },
  },
  {
    label: "HSS Moderate vs Combined",
    a: {
      name: "Scenario A · HSS Moderate",
      hss: { enabled: true, intensity: "moderate" },
    },
    b: {
      name: "Scenario B · Combined",
      hss: { enabled: true, intensity: "moderate" },
      treatments: { enabled: true, pph_bundle: true, mgso4: true },
      community: {
        enabled: true,
        prompts: { enabled: true, adoption: 0.6, chv_engagement: 0.6 },
        mentors: { enabled: false },
        fqa: { enabled: false, implementation: "low", influence_on_pulse: "low" },
        pulse: { enabled: false, implementation: "low" },
        referral_emt: { enabled: false },
      },
    },
  },
  {
    label: "MOMISH vs HSS + MOMISH",
    a: {
      name: "Scenario A · MOMISH only",
      community: {
        enabled: true,
        prompts: { enabled: true, adoption: 1, chv_engagement: 1, intervention_fidelity: 0.87 },
        mentors: { enabled: true, adoption: 0.8, attendance: 0.8, fidelity: 0.8 },
        fqa: { enabled: false, implementation: "low", influence_on_pulse: "low" },
        pulse: { enabled: false, implementation: "low" },
        referral_emt: { enabled: false },
      },
    },
    b: {
      name: "Scenario B · HSS + MOMISH",
      hss: { enabled: true, intensity: "moderate" },
      community: {
        enabled: true,
        prompts: { enabled: true, adoption: 0.8, chv_engagement: 0.8 },
        mentors: { enabled: true, adoption: 0.8 },
        fqa: { enabled: false, implementation: "low", influence_on_pulse: "low" },
        pulse: { enabled: false, implementation: "low" },
        referral_emt: { enabled: false },
      },
    },
  },
];

export function mergeScenario(base: Scenario, patch: Partial<Scenario>): Scenario {
  return {
    ...DEFAULT_SCENARIO,
    ...base,
    ...patch,
    hss: { ...DEFAULT_SCENARIO.hss, ...base.hss, ...patch.hss },
    treatments: { ...DEFAULT_SCENARIO.treatments, ...base.treatments, ...patch.treatments },
    community: {
      ...DEFAULT_SCENARIO.community,
      ...base.community,
      ...patch.community,
      prompts: {
        ...DEFAULT_SCENARIO.community.prompts,
        ...base.community?.prompts,
        ...patch.community?.prompts,
      },
      mentors: {
        ...DEFAULT_SCENARIO.community.mentors,
        ...base.community?.mentors,
        ...patch.community?.mentors,
      },
      fqa: {
        ...DEFAULT_SCENARIO.community.fqa,
        ...base.community?.fqa,
        ...patch.community?.fqa,
      },
      pulse: {
        ...DEFAULT_SCENARIO.community.pulse,
        ...base.community?.pulse,
        ...patch.community?.pulse,
      },
      referral_emt: {
        ...DEFAULT_SCENARIO.community.referral_emt,
        ...base.community?.referral_emt,
        ...patch.community?.referral_emt,
      },
      blood_tracking: {
        enabled: false,
        level: "current" as const,
        ...DEFAULT_SCENARIO.community.blood_tracking,
        ...base.community?.blood_tracking,
        ...patch.community?.blood_tracking,
      },
    },
    run: { ...DEFAULT_SCENARIO.run, ...base.run, ...patch.run },
    ui_levels: { ...base.ui_levels, ...patch.ui_levels },
  };
}
