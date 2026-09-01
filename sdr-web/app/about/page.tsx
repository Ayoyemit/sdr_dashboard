"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { aboutBackLabel, safeReturnPath } from "@/lib/about-nav";

const SECTION_IDS = ["structure", "assumptions", "data", "literature"] as const;

function AboutContent() {
  const { t } = useLocale();
  const searchParams = useSearchParams();
  const returnTo = safeReturnPath(searchParams.get("returnTo"));
  const backHref = returnTo ?? "/";
  const backLabel = aboutBackLabel(returnTo, t);

  const sections = SECTION_IDS.map((id) => ({
    id,
    title: t(`about.sections.${id}.title`),
    body: t(`about.sections.${id}.body`),
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 md:px-8 py-6 md:py-8">
      <div className="grid lg:grid-cols-4 gap-8">
        <nav className="hidden lg:block lg:sticky lg:top-24 h-fit">
          <h2 className="text-[11px] uppercase tracking-widest text-ink-muted mb-3">
            {t("about.onThisPage")}
          </h2>
          <ul className="space-y-2 text-sm mb-6">
            {sections.map((s) => (
              <li key={s.id}>
                <a href={`#${s.id}`} className="text-ink-soft hover:text-accent">
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
          <Link
            href={backHref}
            className="inline-flex items-center gap-1 text-sm text-ink-muted hover:text-accent"
          >
            {backLabel}
          </Link>
        </nav>
        <div className="lg:col-span-3">
          <Link
            href={backHref}
            className="lg:hidden inline-flex items-center gap-1 text-sm text-accent hover:underline mb-4 min-h-[44px]"
          >
            {backLabel}
          </Link>

          <h1 className="font-display text-3xl sm:text-4xl mb-4 sm:mb-6">{t("about.title")}</h1>

          <nav
            className="lg:hidden flex gap-2 overflow-x-auto scrollbar-none pb-4 mb-6 -mx-1 px-1"
            aria-label={t("about.onThisPage")}
          >
            {sections.map((s) => (
              <a
                key={s.id}
                href={`#${s.id}`}
                className="shrink-0 min-h-[44px] inline-flex items-center px-4 py-2 text-sm rounded-full border border-border bg-card hover:bg-paper-deep transition"
              >
                {s.title}
              </a>
            ))}
          </nav>

          {sections.map((s) => (
            <section key={s.id} id={s.id} className="mb-10 scroll-mt-24">
              <h2 className="font-display text-xl sm:text-2xl mb-3">{s.title}</h2>
              <p className="text-ink-soft leading-relaxed text-sm sm:text-base">{s.body}</p>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function AboutPage() {
  return (
    <Suspense fallback={<div className="max-w-7xl mx-auto px-4 md:px-8 py-8 text-ink-muted">…</div>}>
      <AboutContent />
    </Suspense>
  );
}
