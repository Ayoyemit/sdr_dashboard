"use client";

import { useMemo, useState } from "react";
import { useCounty } from "@/components/county/CountyProvider";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { getCountyById, getCountyLabel, isCountySelectable } from "@/lib/counties";
import {
  KAKAMEGA_MAP_POINT,
  KENYA_COUNTY_PATHS,
  KENYA_MAP_VIEWBOX,
} from "@/lib/data/kenya-county-paths";

interface Props {
  compact?: boolean;
}

export default function KenyaCountyMap({ compact = false }: Props) {
  const { t } = useLocale();
  const { countyId, setCountyId, comingSoonCountyId, clearComingSoon } = useCounty();
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [tappedId, setTappedId] = useState<string | null>(null);

  const activeId = hoveredId ?? tappedId;
  const hovered = activeId ? getCountyById(activeId) : null;
  const hoveredName = activeId ? getCountyLabel(activeId) : null;
  const selected = getCountyById(countyId);

  const sortedPaths = useMemo(
    () =>
      [...KENYA_COUNTY_PATHS].sort((a, b) => {
        if (a.id === countyId) return 1;
        if (b.id === countyId) return -1;
        return 0;
      }),
    [countyId]
  );

  const handleCountySelect = (id: string) => {
    setTappedId(id);
    setCountyId(id);
  };

  return (
    <div className={`relative w-full ${compact ? "h-full min-h-0 flex flex-col" : ""}`}>
      <div
        className={`rounded-2xl border border-border bg-gradient-to-br from-paper-deep/80 to-card shadow-[0_20px_50px_rgba(28,26,21,0.06)] flex flex-col min-h-0 ${
          compact ? "h-full p-3 md:p-4" : "p-4 md:p-6"
        }`}
      >
        <div className={`flex items-start justify-between gap-2 shrink-0 ${compact ? "mb-2" : "mb-4"}`}>
          <div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-accent mb-0.5">
              {t("start.mapTitle")}
            </div>
            {!compact && (
              <p className="text-xs text-ink-muted max-w-xs leading-relaxed">{t("start.mapHint")}</p>
            )}
            {compact && (
              <p className="text-[10px] text-ink-muted mt-0.5 md:hidden">{t("start.mapHint")}</p>
            )}
          </div>
          {selected?.calibrated && (
            <span className="shrink-0 text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded-md bg-intervention-soft text-intervention border border-intervention/20">
              {t("start.calibrated")}
            </span>
          )}
        </div>

        <div
          className={`relative mx-auto w-full min-h-0 ${
            compact ? "flex-1 min-h-[200px]" : "aspect-[8/9] max-h-[420px]"
          }`}
        >
          <svg
            viewBox={KENYA_MAP_VIEWBOX}
            className="w-full h-full touch-manipulation"
            preserveAspectRatio="xMidYMid meet"
            role="img"
            aria-label={t("start.mapAria")}
          >
            <defs>
              <pattern id="map-grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path
                  d="M 40 0 L 0 0 0 40"
                  fill="none"
                  stroke="rgba(28,26,21,0.04)"
                  strokeWidth="1"
                />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#map-grid)" />

            {sortedPaths.map((county) => {
              const calibrated = isCountySelectable(county.id);
              const isSelected = county.id === countyId;
              const isHovered = county.id === activeId;

              return (
                <path
                  key={county.id}
                  d={county.d}
                  className="transition-all duration-200 cursor-pointer"
                  fill={
                    isSelected
                      ? "rgba(181, 71, 31, 0.55)"
                      : isHovered && calibrated
                        ? "rgba(46, 95, 92, 0.35)"
                        : isHovered
                          ? "rgba(156, 144, 130, 0.35)"
                          : calibrated
                            ? "rgba(46, 95, 92, 0.18)"
                            : "rgba(156, 144, 130, 0.14)"
                  }
                  stroke={
                    isSelected
                      ? "#B5471F"
                      : isHovered
                        ? "#2E5F5C"
                        : "rgba(28, 26, 21, 0.12)"
                  }
                  strokeWidth={isSelected ? 2.2 : isHovered ? 1.6 : 0.8}
                  onMouseEnter={() => setHoveredId(county.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  onFocus={() => setHoveredId(county.id)}
                  onBlur={() => setHoveredId(null)}
                  onClick={() => handleCountySelect(county.id)}
                  onTouchEnd={(e) => {
                    e.preventDefault();
                    handleCountySelect(county.id);
                  }}
                  tabIndex={0}
                  aria-label={county.name}
                />
              );
            })}

            <circle
              cx={KAKAMEGA_MAP_POINT.x}
              cy={KAKAMEGA_MAP_POINT.y}
              r={countyId === "kakamega" ? 6 : 5}
              fill={countyId === "kakamega" ? "#B5471F" : "#2E5F5C"}
              stroke="#fdfbf7"
              strokeWidth="1.5"
              className="pointer-events-none"
            />
          </svg>

          {(activeId || countyId) && (
            <div className="pointer-events-none absolute inset-x-0 bottom-0 sm:left-2 sm:bottom-2 sm:right-2">
              <div className="rounded-t-lg sm:rounded-md border border-border bg-card/98 backdrop-blur px-3 py-2.5 shadow-sm sm:max-w-[200px] safe-bottom">
                <span className="font-display text-sm sm:text-xs text-ink block">
                  {hoveredName ?? selected?.name ?? "Kenya"}
                </span>
                <span className="text-[11px] sm:text-[10px] text-ink-muted leading-tight block mt-0.5">
                  {activeId && !isCountySelectable(activeId)
                    ? t("start.comingSoon", {
                        when: hovered?.available ?? t("start.comingSoonShort", { when: "soon" }),
                      })
                    : selected?.population
                      ? t("start.countyPop", {
                          pop: (selected.population / 1_000_000).toFixed(2),
                        })
                      : t("start.calibrated")}
                </span>
              </div>
            </div>
          )}
        </div>

        {comingSoonCountyId && (
          <div className="mt-2 shrink-0 flex items-start justify-between gap-2 rounded-lg border border-warning/30 bg-warning/10 px-2 py-2 text-[10px] text-ink-soft min-h-[44px]">
            <span>
              {(() => {
                const meta = getCountyById(comingSoonCountyId);
                const name = getCountyLabel(comingSoonCountyId);
                return meta?.available
                  ? t("start.countyComingWhen", { name, when: meta.available })
                  : t("start.countyNotCalibrated", { name });
              })()}
            </span>
            <button
              type="button"
              onClick={clearComingSoon}
              className="shrink-0 min-w-[44px] min-h-[44px] flex items-center justify-center text-ink-muted hover:text-ink -mr-2"
              aria-label={t("nav.close")}
            >
              ×
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
