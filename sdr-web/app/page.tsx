"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useCounty } from "@/components/county/CountyProvider";
import { useLocale } from "@/components/i18n/LocaleProvider";
import KenyaCountyMap from "@/components/landing/KenyaCountyMap";
import { fetchPresets } from "@/lib/api";
import { getPresetDisplay, PRESET_DISPLAY_ORDER } from "@/lib/preset-labels";
import { Preset } from "@/lib/scenarios";
import { designHref } from "@/lib/url-state";

export default function StartPage() {
  const { t } = useLocale();
  const { county, countyId } = useCounty();
  const [presets, setPresets] = useState<Preset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPresets()
      .then(setPresets)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const featuredPreset = useMemo(
    () => presets.find((p) => p.id === "combined") ?? presets[0],
    [presets]
  );

  const orderedPresets = useMemo(() => {
    const byId = new Map(presets.map((p) => [p.id, p]));
    const cards: Array<{ id: string; preset?: Preset; isCustom?: boolean }> =
      PRESET_DISPLAY_ORDER.map((id) => {
        if (id === "custom") return { id, isCustom: true };
        const preset = byId.get(id);
        return preset ? { id, preset } : { id };
      }).filter((c) => c.isCustom || c.preset);
    return cards;
  }, [presets]);

  const countyLabel = county.population
    ? t("start.countyActive", {
        name: county.name,
        pop: (county.population / 1_000_000).toFixed(2),
      })
    : t("start.county");

  return (
    <div className="landing-page mx-auto max-w-7xl px-4 md:px-8">
      <section className="landing-hero grid lg:grid-cols-2 gap-8 lg:gap-10 items-stretch mb-8 lg:mb-4 lg:min-h-0">
        <div className="flex flex-col justify-center gap-5 lg:gap-6 lg:py-2 lg:min-h-0">
          <div className="space-y-3 lg:space-y-4">
            <p className="inline-flex w-fit items-center rounded-full border border-accent/25 bg-accent/5 px-2.5 py-0.5 text-[10px] uppercase tracking-[0.2em] text-accent">
              {countyLabel}
            </p>
            <h1 className="font-display text-2xl sm:text-3xl xl:text-[2.35rem] font-medium leading-[1.1] tracking-tight max-w-xl">
              {t("start.hero")}
            </h1>
            <p className="text-ink-soft text-sm sm:text-base leading-relaxed max-w-lg lg:line-clamp-3">
              {t("start.lead")}
            </p>
          </div>

          {featuredPreset && (
            <div className="flex flex-wrap items-center gap-3">
              <Link
                href={designHref(countyId, featuredPreset.scenario)}
                className="inline-flex items-center gap-2 min-h-[44px] px-5 py-2.5 bg-ink text-paper rounded-lg text-sm font-medium hover:opacity-90 transition shadow-sm"
              >
                {t("start.featuredCta")}
                <span aria-hidden>→</span>
              </Link>
              <Link
                href={designHref(countyId)}
                className="text-sm text-ink-muted hover:text-accent underline underline-offset-4 transition"
              >
                {t("start.customAlt")}
              </Link>
            </div>
          )}
        </div>

        <div className="min-h-[280px] sm:min-h-[320px] lg:min-h-0 lg:h-full">
          <KenyaCountyMap compact fillHeight />
        </div>
      </section>

      <section className="landing-presets lg:border-t lg:border-border/60 lg:pt-4">
        <div className="mb-3 lg:mb-2.5 flex flex-col gap-1 sm:flex-row sm:flex-wrap sm:items-baseline sm:justify-between sm:gap-x-4">
          <h2 className="font-display text-lg lg:text-xl">{t("start.presets")}</h2>
          <p className="text-xs sm:text-sm text-ink-muted max-w-md leading-snug">
            {t("start.presetsHint")}{" "}
            <Link href={designHref(countyId)} className="underline underline-offset-2 hover:text-accent">
              {t("start.buildFromScratch")}
            </Link>
          </p>
        </div>

        {loading ? (
          <p className="text-sm text-ink-muted">{t("start.loadingPresets")}</p>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {orderedPresets.map((card) => {
              if (card.isCustom) {
                const display = getPresetDisplay("custom", t);
                return (
                  <Link
                    key="custom"
                    href={designHref(countyId)}
                    className="preset-card group block bg-card border border-border rounded-xl p-4 lg:p-3.5 min-h-[108px] lg:min-h-[100px]"
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3 className="font-display text-sm lg:text-[15px] leading-snug line-clamp-2">
                        {display?.name}
                      </h3>
                      <span className="preset-card-arrow text-accent shrink-0 text-sm" aria-hidden>
                        →
                      </span>
                    </div>
                    <p className="text-[11px] text-ink-muted mb-1 line-clamp-1">{display?.subtitle}</p>
                    <p className="text-xs text-ink-soft leading-snug line-clamp-2 hidden sm:block">
                      {display?.description}
                    </p>
                  </Link>
                );
              }

              const preset = card.preset!;
              const display = getPresetDisplay(preset.id, t);
              const isRecommended = preset.is_recommended || preset.id === "combined";

              return (
                <Link
                  key={preset.id}
                  href={designHref(countyId, preset.scenario)}
                  className={`preset-card group block bg-card border rounded-xl p-4 lg:p-3.5 min-h-[108px] lg:min-h-[100px] ${
                    isRecommended ? "border-accent/50 ring-1 ring-accent/20" : "border-border"
                  }`}
                >
                  {isRecommended && (
                    <span className="text-[9px] uppercase tracking-widest text-accent font-medium mb-1 block">
                      {t("start.recommended")}
                    </span>
                  )}
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <h3 className="font-display text-sm lg:text-[15px] leading-snug line-clamp-2">
                      {display?.name ?? preset.name}
                    </h3>
                    <span className="preset-card-arrow text-accent shrink-0 text-sm" aria-hidden>
                      →
                    </span>
                  </div>
                  <p className="text-[11px] text-ink-muted mb-1 line-clamp-1">
                    {display?.subtitle ?? preset.subtitle}
                  </p>
                  <p className="text-xs text-ink-soft leading-snug line-clamp-2 hidden sm:block">
                    {display?.description ?? preset.description}
                  </p>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
