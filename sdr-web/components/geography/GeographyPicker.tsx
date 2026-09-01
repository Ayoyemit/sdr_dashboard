"use client";

import { useLocale } from "@/components/i18n/LocaleProvider";
import { COUNTIES, CountyMeta, formatCountyPopulation } from "@/lib/counties";
import { SupportedCountyId } from "@/lib/scenarios";

export type GeographyPickerMode = "select" | "rerun";

interface Props {
  value: SupportedCountyId;
  onChange?: (countyId: SupportedCountyId) => void;
  mode?: GeographyPickerMode;
  runningCountyId?: SupportedCountyId | null;
  disabled?: boolean;
  compact?: boolean;
}

function CountyChip({
  county,
  active,
  disabled,
  running,
  onClick,
  compact,
  t,
}: {
  county: CountyMeta;
  active: boolean;
  disabled: boolean;
  running: boolean;
  onClick: () => void;
  compact?: boolean;
  t: (key: string, params?: Record<string, string | number>) => string;
}) {
  const population = formatCountyPopulation(county.population);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || running}
      aria-pressed={active}
      className={[
        "text-left rounded-xl border transition min-h-[44px]",
        compact ? "px-3 py-2" : "px-4 py-3",
        active
          ? "border-accent bg-accent/10 ring-1 ring-accent/30"
          : "border-border bg-card hover:bg-paper-deep hover:border-accent/30",
        disabled ? "opacity-60 cursor-default" : "",
        running ? "opacity-70 cursor-wait" : "",
      ].join(" ")}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-sm">{county.name}</span>
        {active && (
          <span className="text-[10px] uppercase tracking-wide text-accent font-medium">
            {t("geography.currentRun")}
          </span>
        )}
        {running && (
          <span className="text-[10px] text-ink-muted">{t("geography.runningShort")}</span>
        )}
      </div>
      {!compact && population && (
        <p className="text-[11px] text-ink-muted mt-1">
          {t("geography.population", { population })} · {t("geography.calibrated")}
        </p>
      )}
    </button>
  );
}

export default function GeographyPicker({
  value,
  onChange,
  mode = "select",
  runningCountyId = null,
  disabled = false,
  compact = false,
}: Props) {
  const { t } = useLocale();

  return (
    <div
      className={compact ? "flex flex-wrap gap-2" : "grid grid-cols-1 sm:grid-cols-2 gap-2"}
      role={mode === "select" ? "radiogroup" : "group"}
      aria-label={t("geography.title")}
    >
      {COUNTIES.map((county) => {
        const id = county.id as SupportedCountyId;
        const active = value === id;
        const isRunning = runningCountyId === id;
        const chipDisabled =
          disabled || isRunning || (mode === "rerun" && active) || !county.calibrated;

        return (
          <CountyChip
            key={county.id}
            county={county}
            active={active}
            disabled={chipDisabled}
            running={isRunning}
            compact={compact}
            t={t}
            onClick={() => {
              if (chipDisabled) return;
              onChange?.(id);
            }}
          />
        );
      })}
    </div>
  );
}
