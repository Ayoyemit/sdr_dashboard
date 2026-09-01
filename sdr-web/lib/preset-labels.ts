import { TranslateFn } from "./i18n";

const PRESET_I18N_KEY: Record<string, string> = {
  "hss-intensive": "hssIntensive",
  momish: "momish",
  combined: "combined",
  custom: "custom",
};

/** Display order for start page preset cards */
export const PRESET_DISPLAY_ORDER = ["combined", "hss-intensive", "momish", "custom"] as const;

export interface PresetDisplay {
  name: string;
  subtitle: string;
  description: string;
}

export function getPresetDisplay(presetId: string, t: TranslateFn): PresetDisplay | null {
  const key = PRESET_I18N_KEY[presetId];
  if (!key) return null;
  return {
    name: t(`presetCards.${key}.name`),
    subtitle: t(`presetCards.${key}.subtitle`),
    description: t(`presetCards.${key}.description`),
  };
}
