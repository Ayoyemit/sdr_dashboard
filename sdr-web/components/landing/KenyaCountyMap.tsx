"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useCounty } from "@/components/county/CountyProvider";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { getCountyById, getCountyLabel, isCountySelectable } from "@/lib/counties";
import {
  COUNTY_MAP_POINTS,
  KENYA_COUNTY_PATHS,
  KENYA_MAP_VIEWBOX,
} from "@/lib/data/kenya-county-paths";
import { designHref } from "@/lib/url-state";

interface Props {
  compact?: boolean;
  /** Stretch map card to fill parent height (landing hero on desktop) */
  fillHeight?: boolean;
}

export default function KenyaCountyMap({ compact = false, fillHeight = false }: Props) {
  const { t } = useLocale();
  const { countyId, setCountyId, comingSoonCountyId, clearComingSoon } = useCounty();
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [tappedId, setTappedId] = useState<string | null>(null);

  const activeId = hoveredId ?? tappedId;
  const hovered = activeId ? getCountyById(activeId) : null;
  const hoveredName = activeId ? getCountyLabel(activeId) : null;
  const selected = getCountyById(countyId);
  const displayCounty = activeId ? hovered : selected;

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

  const mapPoint = COUNTY_MAP_POINTS[countyId] ?? COUNTY_MAP_POINTS.kakamega;

  const countyDetail =
    activeId && !isCountySelectable(activeId)
      ? t("start.comingSoon", {
          when: hovered?.available ?? t("start.comingSoonShort", { when: "soon" }),
        })
      : displayCounty?.population
        ? t("start.countyPop", {
            pop: (displayCounty.population / 1_000_000).toFixed(2),
          })
        : t("start.calibrated");

  const useFillLayout = compact && fillHeight;

  return (
    <div
      className={`relative w-full ${
        useFillLayout ? "h-full min-h-0 flex flex-col" : compact ? "flex flex-col" : ""
      }`}
    >
      <div
        className={`rounded-2xl border border-border bg-gradient-to-br from-paper-deep/80 to-card shadow-[0_20px_50px_rgba(28,26,21,0.06)] flex flex-col min-h-0 ${
          useFillLayout
            ? "h-full p-3 md:p-4 gap-2.5"
            : compact
              ? "p-4 sm:p-5 gap-4"
              : "p-4 md:p-6 gap-4"
        }`}
      >
        <div className="flex items-start justify-between gap-3 shrink-0">
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-[0.2em] text-accent mb-0.5">
              {t("start.mapTitle")}
            </div>
            <p
              className={`text-ink-muted leading-snug ${
                useFillLayout
                  ? "hidden lg:block text-[10px] line-clamp-1"
                  : "text-xs sm:text-sm max-w-[16rem]"
              }`}
            >
              {t("start.mapHint")}
            </p>
            {!useFillLayout && (
              <p className="text-[10px] text-ink-muted mt-0.5 lg:hidden">{t("start.mapHint")}</p>
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
            useFillLayout
              ? "flex-1 min-h-[180px]"
              : compact
                ? "aspect-[4/5] max-h-[380px] sm:max-h-[420px]"
                : "aspect-[8/9] max-h-[420px]"
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

              let fill: string;
              let stroke: string;
              let strokeWidth: number;

              if (isSelected) {
                fill = "rgba(181, 71, 31, 0.58)";
                stroke = "#B5471F";
                strokeWidth = 2.4;
              } else if (isHovered && calibrated) {
                fill = "rgba(46, 95, 92, 0.5)";
                stroke = "#2E5F5C";
                strokeWidth = 1.8;
              } else if (isHovered) {
                fill = "rgba(156, 144, 130, 0.3)";
                stroke = "rgba(28, 26, 21, 0.25)";
                strokeWidth = 1.2;
              } else if (calibrated) {
                fill = "rgba(46, 95, 92, 0.34)";
                stroke = "rgba(46, 95, 92, 0.65)";
                strokeWidth = 1.3;
              } else {
                fill = "rgba(156, 144, 130, 0.1)";
                stroke = "rgba(28, 26, 21, 0.08)";
                strokeWidth = 0.7;
              }

              return (
                <path
                  key={county.id}
                  d={county.d}
                  className="transition-all duration-200 cursor-pointer"
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={strokeWidth}
                  onMouseEnter={() => setHoveredId(county.id)}
                  onMouseLeave={() => setHoveredId(null)}
                  onFocus={() => setHoveredId(county.id)}
                  onBlur={() => setHoveredId(null)}
                  onClick={() => handleCountySelect(county.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleCountySelect(county.id);
                    }
                  }}
                  onTouchEnd={(e) => {
                    e.preventDefault();
                    handleCountySelect(county.id);
                  }}
                  tabIndex={0}
                  role="button"
                  aria-pressed={isSelected}
                  aria-label={county.name}
                  aria-disabled={!calibrated}
                />
              );
            })}

            {mapPoint && (
              <circle
                cx={mapPoint.x}
                cy={mapPoint.y}
                r={6}
                fill="#B5471F"
                stroke="#fdfbf7"
                strokeWidth="1.5"
                className="pointer-events-none"
              />
            )}
          </svg>
        </div>

        <div
          className={`shrink-0 rounded-lg border border-border-soft bg-paper-deep/50 ${
            useFillLayout ? "px-3 py-2" : "rounded-xl px-4 py-3.5"
          }`}
        >
          <div className="flex items-baseline justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[9px] uppercase tracking-wider text-ink-muted">
                {t("start.selectCounty")}
              </div>
              <div className={`font-display text-ink truncate ${useFillLayout ? "text-sm" : "text-base"}`}>
                {hoveredName ?? selected?.name ?? "Kenya"}
              </div>
            </div>
            <p className="text-[11px] text-ink-muted leading-snug text-right shrink-0 max-w-[45%]">
              {countyDetail}
            </p>
          </div>
          {isCountySelectable(countyId) && (
            <Link
              href={designHref(countyId)}
              className="mt-2.5 inline-flex w-full sm:w-auto items-center justify-center min-h-[40px] px-4 py-2 rounded-lg bg-ink text-paper text-sm font-medium hover:opacity-90 transition"
            >
              {t("start.mapContinue", { county: selected?.name ?? countyId })}
            </Link>
          )}
        </div>

        {comingSoonCountyId && (
          <div className="shrink-0 flex items-start justify-between gap-2 rounded-lg border border-warning/30 bg-warning/10 px-2.5 py-2 text-[10px] text-ink-soft">
            <span className="leading-snug">
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
              className="shrink-0 min-w-[36px] min-h-[36px] flex items-center justify-center text-ink-muted hover:text-ink -mr-1"
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
