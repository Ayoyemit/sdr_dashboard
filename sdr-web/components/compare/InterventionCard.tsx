"use client";

import Link from "next/link";
import PillSelector from "@/components/PillSelector";
import { useLocale } from "@/components/i18n/LocaleProvider";
import {
  getLibraryItem,
  HSS_COMPARE_OPTIONS,
  InterventionId,
  MOMISH_OPTIONS,
  MomishLevel,
  SINGLE_COMPARE_OPTIONS,
  SingleInterventionLevel,
} from "@/lib/interventions";
import { HSSIntensity } from "@/lib/scenarios";

interface Props {
  id: InterventionId;
  hssIntensity?: HSSIntensity;
  singleLevel?: SingleInterventionLevel;
  momishLevel?: MomishLevel;
  onHssChange?: (intensity: HSSIntensity) => void;
  onSingleChange?: (level: SingleInterventionLevel) => void;
  onMomishChange?: (level: MomishLevel) => void;
  onRemove: () => void;
}

export default function InterventionCard({
  id,
  hssIntensity,
  singleLevel,
  momishLevel,
  onHssChange,
  onSingleChange,
  onMomishChange,
  onRemove,
}: Props) {
  const { t } = useLocale();
  const item = getLibraryItem(id);

  const hssOptions = HSS_COMPARE_OPTIONS.map((o) => ({
    value: o.value,
    label: t(o.labelKey),
  }));

  const singleOptions = SINGLE_COMPARE_OPTIONS.map((o) => ({
    value: o.value,
    label: t(o.labelKey),
  }));

  const momishOpts = MOMISH_OPTIONS.map((o) => ({
    value: o.value,
    label: t(o.labelKey),
  }));

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-start justify-between mb-1">
        <div>
          <h4 className="text-sm font-medium flex items-center gap-2">
            {item.name}
            {item.wired === "ui-only" && (
              <span className="text-[9px] text-warning">● {t("common.uiOnly")}</span>
            )}
            {item.wired === "partial" && (
              <span className="text-[9px] text-warning">● partial</span>
            )}
          </h4>
          <p className="text-[11px] text-ink-muted mt-0.5">{item.description}</p>
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="text-ink-muted hover:text-ink text-lg leading-none px-1"
          aria-label={`Remove ${item.name}`}
        >
          ×
        </button>
      </div>

      {id === "hss" && onHssChange && (
        <div className="mt-3">
          <PillSelector
            options={hssOptions}
            value={hssIntensity ?? "moderate"}
            onChange={(v) => onHssChange(v as HSSIntensity)}
          />
        </div>
      )}

      {item.group === "single" && onSingleChange && (
        <div className="mt-3">
          <PillSelector
            options={singleOptions}
            value={singleLevel === "off" ? "current" : (singleLevel ?? "current")}
            onChange={(v) => onSingleChange(v as SingleInterventionLevel)}
          />
        </div>
      )}

      {item.group === "momish" && onMomishChange && (
        <div className="mt-3">
          <PillSelector
            options={momishOpts}
            value={momishLevel ?? "off"}
            onChange={(v) => onMomishChange(v as MomishLevel)}
          />
        </div>
      )}
    </div>
  );
}
