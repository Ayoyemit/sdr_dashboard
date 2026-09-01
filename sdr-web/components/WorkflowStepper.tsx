"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useLocale } from "@/components/i18n/LocaleProvider";

export type WorkflowStepId =
  | "start"
  | "design"
  | "run"
  | "results"
  | "compare"
  | "compareResults";

type StepperVariant = "single" | "compare";

interface StepDef {
  id: WorkflowStepId;
  href: string;
  label: string;
}

interface Props {
  resultsHref?: string;
  compareHref?: string;
  variant?: StepperVariant;
}

function stepIndex(id: WorkflowStepId, variant: StepperVariant): number {
  if (variant === "compare") {
    return { start: 0, design: 1, run: 1, compare: 2, results: 3, compareResults: 3 }[id];
  }
  return { start: 0, design: 1, run: 2, results: 3, compare: 1, compareResults: 3 }[id];
}

export default function WorkflowStepper({
  resultsHref = "/results",
  compareHref = "/compare/results",
  variant = "single",
}: Props) {
  const { t } = useLocale();
  const pathname = usePathname();
  const [hash, setHash] = useState("");

  useEffect(() => {
    const sync = () => setHash(window.location.hash);
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, [pathname]);

  const steps: StepDef[] =
    variant === "compare"
      ? [
          { id: "start", href: "/", label: t("nav.start") },
          { id: "design", href: "/design", label: t("nav.designShort") },
          { id: "compare", href: "/compare", label: t("nav.compareStep") },
          {
            id: "compareResults",
            href: compareHref,
            label: t("nav.compareResults"),
          },
        ]
      : [
          { id: "start", href: "/", label: t("nav.start") },
          { id: "design", href: "/design", label: t("nav.designShort") },
          { id: "run", href: "/design#run-settings", label: t("nav.run") },
          { id: "results", href: resultsHref, label: t("nav.results") },
        ];

  let active: WorkflowStepId;
  if (variant === "compare") {
    active = pathname.startsWith("/compare/results") ? "compareResults" : "compare";
    if (pathname === "/compare") active = "compare";
  } else if (pathname.startsWith("/results")) {
    active = "results";
  } else if (pathname.startsWith("/design")) {
    active = hash === "#run-settings" ? "run" : "design";
  } else {
    active = "start";
  }

  const activeIdx = stepIndex(active, variant);

  return (
    <nav
      className="hidden lg:flex items-center gap-1 min-w-0"
      aria-label={t("nav.workflow")}
    >
      {steps.map((step, i) => {
        const done = i < activeIdx;
        const isActive = stepIndex(step.id, variant) === activeIdx;
        return (
          <span key={step.id} className="flex items-center shrink-0">
            {i > 0 && <span className="text-ink-muted/40 px-1 text-xs select-none">·</span>}
            <Link
              href={step.href}
              aria-current={isActive ? "step" : undefined}
              className={`inline-flex items-center gap-1.5 min-h-[44px] px-2 py-1 rounded-md text-xs whitespace-nowrap transition ${
                isActive
                  ? "bg-card text-ink font-medium shadow-sm border border-border/60"
                  : done
                    ? "text-ink-soft hover:text-ink"
                    : "text-ink-muted hover:text-ink-soft"
              }`}
            >
              <span
                className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-medium border ${
                  isActive
                    ? "border-accent text-accent bg-accent/10"
                    : done
                      ? "border-intervention/40 text-intervention bg-intervention-soft/30"
                      : "border-border text-ink-muted"
                }`}
              >
                {done && !isActive ? "✓" : i + 1}
              </span>
              {step.label}
            </Link>
          </span>
        );
      })}
    </nav>
  );
}
