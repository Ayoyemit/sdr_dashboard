"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import CountyDropdown from "@/components/CountyDropdown";
import LanguageToggle from "@/components/i18n/LanguageToggle";
import GeographyBadge from "@/components/geography/GeographyBadge";
import NavOverflowMenu from "@/components/NavOverflowMenu";
import SdrLogoMark from "@/components/SdrLogoMark";
import WorkflowStepper from "@/components/WorkflowStepper";
import { useCounty } from "@/components/county/CountyProvider";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { getLastCompareResultsHref, getLastComparisonData } from "@/lib/compare-storage";
import { aboutBackLabel, aboutHref, getCurrentReturnPath, safeReturnPath } from "@/lib/about-nav";
import { getLastResultsHref } from "@/lib/last-run-storage";
import { scenarioFromURLParams } from "@/lib/url-state";
import { SupportedCountyId } from "@/lib/scenarios";

type NavMode = "minimal" | "workflow" | "compare";

interface StepDef {
  href: string;
  label: string;
}

function getNavMode(pathname: string): NavMode {
  if (pathname === "/" || pathname === "/about") return "minimal";
  if (pathname.startsWith("/compare")) return "compare";
  return "workflow";
}

function NavLogo({ compact = false }: { compact?: boolean }) {
  const { county } = useCounty();
  const title = compact ? `${county.name} Decision Tool` : `${county.name} Decision Tool`;

  return (
    <Link href="/" className="flex items-center gap-2.5 shrink-0 min-w-0 min-h-[44px]">
      <div className="w-8 h-8 rounded-md bg-paper-deep border border-border flex items-center justify-center shrink-0">
        <SdrLogoMark />
      </div>
      {!compact ? (
        <div className="leading-tight hidden sm:block min-w-0">
          <div className="text-[11px] tracking-[0.18em] text-ink-muted uppercase truncate">
            Service Delivery Redesign
          </div>
          <div className="font-display text-[15px] font-medium truncate">{title}</div>
        </div>
      ) : (
        <span className="font-display text-sm font-medium hidden sm:inline truncate">{title}</span>
      )}
    </Link>
  );
}

function MobileStepLabel({ steps, activeHref }: { steps: StepDef[]; activeHref: string }) {
  const active = steps.find((s) => s.href === activeHref) ?? steps[0];
  return (
    <span className="md:hidden text-sm font-medium text-ink truncate max-w-[8rem] sm:max-w-none">
      {active?.label}
    </span>
  );
}

function ShareModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useLocale();
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-ink/40 p-0 sm:p-4 safe-bottom">
      <div className="bg-card border border-border rounded-t-xl sm:rounded-lg p-6 max-w-md w-full shadow-xl max-h-[90dvh] overflow-y-auto">
        <h3 className="font-display text-lg mb-2">{t("nav.shareTitle")}</h3>
        <p className="text-sm text-ink-muted mb-4">{t("nav.shareHint")}</p>
        <input
          readOnly
          value={typeof window !== "undefined" ? window.location.href : ""}
          className="w-full text-xs border border-border rounded px-3 py-2 mb-4 bg-paper-deep"
        />
        <button
          type="button"
          onClick={onClose}
          className="w-full min-h-[44px] py-2 bg-ink text-paper rounded-md text-sm"
        >
          {t("nav.close")}
        </button>
      </div>
    </div>
  );
}

function MinimalNavBar({ trailing }: { trailing: React.ReactNode }) {
  return (
    <header className="border-b border-border/60 bg-paper/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-3 flex items-center justify-between gap-4">
        <NavLogo compact />
        <div className="flex items-center gap-2 shrink-0">{trailing}</div>
      </div>
    </header>
  );
}

function WorkflowNavBar({
  resultsHref,
  compareHref,
  aboutLink,
  showCompareLink,
  showShare,
  mobileSteps,
  mobileActiveHref,
  showCountySwitcher,
  resultsCountyId,
  compareCountyId,
}: {
  resultsHref: string;
  compareHref: string;
  aboutLink: string;
  showCompareLink: boolean;
  showShare: boolean;
  mobileSteps: StepDef[];
  mobileActiveHref: string;
  showCountySwitcher: boolean;
  resultsCountyId?: string | null;
  compareCountyId?: SupportedCountyId | null;
}) {
  const { t } = useLocale();
  const [shareOpen, setShareOpen] = useState(false);
  const stepperVariant = compareCountyId != null ? "compare" : "single";

  return (
    <>
      <header className="border-b border-border bg-paper/95 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-2.5 flex items-center gap-2 sm:gap-3">
          <NavLogo compact />

          <MobileStepLabel steps={mobileSteps} activeHref={mobileActiveHref} />

          <div className="flex-1 flex justify-center min-w-0 px-1">
            <WorkflowStepper
              variant={stepperVariant}
              resultsHref={resultsHref}
              compareHref={compareHref}
            />
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {showCountySwitcher ? (
              <CountyDropdown />
            ) : compareCountyId ? (
              <GeographyBadge countyId={compareCountyId} titleKey="geography.compareLocked" />
            ) : resultsCountyId ? (
              <GeographyBadge countyId={resultsCountyId as SupportedCountyId} />
            ) : null}
            <LanguageToggle />
            <Link
              href={aboutLink}
              className="hidden sm:inline-flex min-h-[44px] items-center px-2.5 py-1 text-xs border border-border rounded-md text-ink-muted hover:text-ink hover:bg-paper-deep transition whitespace-nowrap"
            >
              {t("nav.help")}
            </Link>
            <NavOverflowMenu
              compareHref={compareHref}
              aboutHref={aboutLink}
              showCompare={showCompareLink}
              showCountySwitcher={showCountySwitcher}
              onShare={showShare ? () => setShareOpen(true) : undefined}
              workflowSteps={mobileSteps}
              activeStepHref={mobileActiveHref}
            />
          </div>
        </div>
      </header>

      <ShareModal open={shareOpen} onClose={() => setShareOpen(false)} />
    </>
  );
}

export default function TopNav() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { t } = useLocale();
  const { countyId } = useCounty();
  const mode = getNavMode(pathname);
  const [resultsHref, setResultsHref] = useState("/results");
  const [compareHref, setCompareHref] = useState("/compare");
  const [compareCountyId, setCompareCountyId] = useState<SupportedCountyId | null>(null);
  const isResultsPage = pathname.startsWith("/results");
  const resultsCountyId = useMemo(() => {
    if (!isResultsPage) return null;
    return scenarioFromURLParams(searchParams.get("s"))?.county ?? null;
  }, [isResultsPage, searchParams]);

  useEffect(() => {
    setResultsHref(getLastResultsHref() ?? "/results");
    setCompareHref(getLastCompareResultsHref() ?? "/compare/results");
    if (!pathname.startsWith("/compare")) {
      setCompareCountyId(null);
      return;
    }
    if (pathname.startsWith("/compare/results")) {
      const last = getLastComparisonData();
      setCompareCountyId((last?.scenario_a?.county as SupportedCountyId) ?? countyId);
    } else {
      setCompareCountyId(countyId);
    }
  }, [pathname, countyId]);

  const workflowSteps: StepDef[] = useMemo(
    () => [
      { href: "/design", label: t("nav.designShort") },
      { href: resultsHref, label: t("nav.results") },
    ],
    [t, resultsHref]
  );

  const compareSteps: StepDef[] = useMemo(
    () => [
      { href: "/design", label: t("nav.designShort") },
      { href: "/compare", label: t("nav.compareStep") },
      {
        href: pathname.startsWith("/compare/results") ? compareHref : "/compare/results",
        label: t("nav.compareResults"),
      },
    ],
    [t, compareHref, pathname]
  );

  const workflowActiveHref = pathname.startsWith("/results") ? resultsHref : "/design";
  const returnPath = getCurrentReturnPath(pathname, searchParams.toString());
  const aboutLink = aboutHref(returnPath || null);
  const aboutReturnTo = safeReturnPath(searchParams.get("returnTo"));

  if (mode === "minimal") {
    const isAbout = pathname === "/about";
    const backHref = isAbout ? (aboutReturnTo ?? "/") : aboutLink;
    const backLabel = isAbout ? aboutBackLabel(aboutReturnTo, t) : t("nav.help");
    return (
      <MinimalNavBar
        trailing={
          <>
            <LanguageToggle />
            {isAbout ? (
              <>
                <span className="px-3 py-1.5 text-sm text-ink font-medium hidden sm:inline">
                  {t("nav.about")}
                </span>
                <Link
                  href={backHref}
                  className="min-h-[44px] inline-flex items-center px-3 py-1.5 text-sm border border-border rounded-md hover:bg-paper-deep transition whitespace-nowrap"
                >
                  {backLabel}
                </Link>
              </>
            ) : (
              <Link
                href={aboutLink}
                className="min-h-[44px] inline-flex items-center px-3 py-1.5 text-sm border border-border rounded-md hover:bg-paper-deep transition whitespace-nowrap"
              >
                <span className="hidden sm:inline">{t("nav.help")}</span>
                <span className="sm:hidden">?</span>
              </Link>
            )}
          </>
        }
      />
    );
  }

  if (mode === "compare") {
    const activeHref = pathname.startsWith("/compare/results") ? compareHref : "/compare";
    return (
      <WorkflowNavBar
        resultsHref={compareHref}
        compareHref={compareHref}
        aboutLink={aboutLink}
        showCompareLink={false}
        showShare
        mobileSteps={compareSteps}
        mobileActiveHref={activeHref}
        showCountySwitcher={false}
        compareCountyId={compareCountyId}
      />
    );
  }

  return (
    <WorkflowNavBar
      resultsHref={resultsHref}
      compareHref={compareHref}
      aboutLink={aboutLink}
      showCompareLink
      showShare
      mobileSteps={workflowSteps}
      mobileActiveHref={workflowActiveHref}
      showCountySwitcher={!isResultsPage}
      resultsCountyId={resultsCountyId}
    />
  );
}
