"use client";

import { useLocale } from "@/components/i18n/LocaleProvider";
import { countyDisplayName, formatCountyPopulation, getCountyById } from "@/lib/counties";
import { SupportedCountyId } from "@/lib/scenarios";

interface Props {
  countyId: SupportedCountyId;
  /** i18n key for tooltip; defaults to geography.resultsLocked */
  titleKey?: string;
}

export default function GeographyBadge({ countyId, titleKey = "geography.resultsLocked" }: Props) {
  const { t } = useLocale();
  const meta = getCountyById(countyId);
  const population = formatCountyPopulation(meta?.population);

  return (
    <div
      className="hidden sm:inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-card/80 text-sm shrink-0"
      title={t(titleKey, { county: countyDisplayName(countyId) })}
    >
      <svg viewBox="0 0 16 16" className="w-3.5 h-3.5 text-accent shrink-0" fill="none" aria-hidden>
        <path
          d="M8 1.5a4 4 0 0 0-4 4c0 3 4 8.5 4 8.5s4-5.5 4-8.5a4 4 0 0 0-4-4Z"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <circle cx="8" cy="5.5" r="1" fill="currentColor" stroke="none" />
      </svg>
      <span className="font-medium">{meta?.name ?? countyId}</span>
      {population && (
        <span className="text-[10px] text-ink-muted hidden md:inline">
          · {t("geography.population", { population })}
        </span>
      )}
    </div>
  );
}
