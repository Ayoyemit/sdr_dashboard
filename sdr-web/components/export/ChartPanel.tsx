"use client";

import { ReactNode, useEffect, useRef, useState } from "react";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { useIsMobile } from "@/lib/use-breakpoint";
import { chartHeight } from "@/lib/chart-labels";
import ChartExportMenu from "./ChartExportMenu";
import ExpandableOverlay, { ExpandButton } from "./ExpandableOverlay";

interface Props {
  chartId: string;
  title: string;
  filename: string;
  height: number;
  children: ReactNode;
  /** Show a small label beside the chart controls (use when there is no section heading) */
  showTitle?: boolean;
  /** Override mobile height; defaults to ~75% of height */
  mobileHeight?: number;
}

function computeExpandedChartHeight(): number {
  if (typeof window === "undefined") return 520;
  return Math.min(Math.max(Math.round(window.innerHeight * 0.62), 360), 640);
}

function ChartShell({
  chartRef,
  chartId,
  title,
  filename,
  pixelHeight,
  children,
}: {
  chartRef: React.RefObject<HTMLDivElement>;
  chartId: string;
  title: string;
  filename: string;
  pixelHeight: number;
  children: ReactNode;
}) {
  return (
    <div
      ref={chartRef}
      data-chart-id={chartId}
      data-chart-title={title}
      data-chart-filename={filename}
      className="chart-export-panel w-full bg-white rounded-md border border-border/40"
      style={{ height: pixelHeight, minHeight: pixelHeight }}
    >
      <div className="w-full" style={{ height: pixelHeight, minHeight: pixelHeight }}>
        {children}
      </div>
    </div>
  );
}

export default function ChartPanel({
  chartId,
  title,
  filename,
  height,
  children,
  showTitle = false,
  mobileHeight,
}: Props) {
  const { t } = useLocale();
  const isMobile = useIsMobile();
  const inlineRef = useRef<HTMLDivElement>(null!);
  const expandedRef = useRef<HTMLDivElement>(null!);
  const [expanded, setExpanded] = useState(false);
  const [expandedReady, setExpandedReady] = useState(false);
  const [expandedHeight, setExpandedHeight] = useState(520);

  const inlineHeight = isMobile ? (mobileHeight ?? chartHeight(height, true)) : height;
  const exportRef = expanded ? expandedRef : inlineRef;

  const openExpanded = () => {
    setExpandedHeight(computeExpandedChartHeight());
    setExpanded(true);
  };

  const closeExpanded = () => {
    setExpanded(false);
    setExpandedReady(false);
  };

  useEffect(() => {
    if (!expanded) return;
    let cancelled = false;
    const frame = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (!cancelled) {
          setExpandedReady(true);
          window.dispatchEvent(new Event("resize"));
        }
      });
    });
    const resizeTimer = window.setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 120);
    return () => {
      cancelled = true;
      cancelAnimationFrame(frame);
      window.clearTimeout(resizeTimer);
    };
  }, [expanded, expandedHeight]);

  return (
    <>
      <div className="flex flex-col">
        <div className="flex items-center justify-between gap-3 mb-3 min-h-[28px]">
          {showTitle ? (
            <span className="text-xs text-ink-muted truncate">{title}</span>
          ) : (
            <span className="sr-only">{title}</span>
          )}
          <div className="flex items-center gap-2 shrink-0">
            <ExpandButton onClick={openExpanded} label={t("charts.expand")} />
            <ChartExportMenu containerRef={exportRef} filenameBase={filename} />
          </div>
        </div>
        <ChartShell
          chartRef={inlineRef}
          chartId={chartId}
          title={title}
          filename={filename}
          pixelHeight={inlineHeight}
        >
          {!expanded ? children : null}
        </ChartShell>
      </div>

      <ExpandableOverlay
        open={expanded}
        onClose={closeExpanded}
        title={title}
        titleId={`chart-dialog-${chartId}`}
        actions={<ChartExportMenu containerRef={expandedRef} filenameBase={filename} />}
      >
        <ChartShell
          chartRef={expandedRef}
          chartId={`${chartId}-expanded`}
          title={title}
          filename={filename}
          pixelHeight={expandedHeight}
        >
          {expanded && expandedReady ? (
            <div key={`${chartId}-expanded-body`} className="w-full h-full">
              {children}
            </div>
          ) : null}
        </ChartShell>
      </ExpandableOverlay>
    </>
  );
}
