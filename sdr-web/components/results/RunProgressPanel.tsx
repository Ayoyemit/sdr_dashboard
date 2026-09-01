"use client";

import { useEffect, useState } from "react";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { countyDisplayName } from "@/lib/counties";
import { Scenario } from "@/lib/scenarios";

interface Props {
  scenario?: Scenario | null;
  mode?: "quick" | "robust";
  estimatedSecondsRemaining?: number | null;
  pollCount?: number;
}

export default function RunProgressPanel({
  scenario,
  mode,
  estimatedSecondsRemaining = null,
  pollCount = 0,
}: Props) {
  const { t } = useLocale();
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const runMode = mode ?? scenario?.run.mode ?? "quick";
  const county = scenario ? countyDisplayName(scenario.county) : undefined;

  return (
    <div className="max-w-lg mx-auto text-center space-y-4" role="status" aria-live="polite">
      <div className="inline-flex h-10 w-10 items-center justify-center rounded-full border-2 border-accent/30 border-t-accent animate-spin" />
      <div>
        <p className="font-display text-lg text-ink">
          {county ? t("geography.running", { county }) : t("results.simulationRunning")}
        </p>
        <p className="text-sm text-ink-muted mt-2 leading-relaxed">
          {runMode === "robust" ? t("results.runProgressRobust") : t("results.runProgressQuick")}
        </p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-3 text-xs text-ink-muted">
          <span className="num">{t("results.elapsed", { seconds: elapsed })}</span>
          {estimatedSecondsRemaining != null && estimatedSecondsRemaining > 0 && (
            <span>· {t("results.estimatedRemaining", { seconds: estimatedSecondsRemaining })}</span>
          )}
          {pollCount > 0 && <span>· {t("results.pollStatus", { count: pollCount })}</span>}
        </div>
      </div>
    </div>
  );
}
