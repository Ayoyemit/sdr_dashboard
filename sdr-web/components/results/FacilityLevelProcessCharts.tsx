"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import ChartPanel from "@/components/export/ChartPanel";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { chartTooltipProps, getChartLayout, xAxisLabel, yAxisLabel } from "@/lib/chart-labels";
import { useIsMobile } from "@/lib/use-breakpoint";
import { ScenarioResult } from "@/lib/scenarios";

type FacilitySnapshot = {
  home: number;
  l23: number;
  l4: number;
  l5: number;
};

interface Props {
  bundle: NonNullable<ScenarioResult["timeseries"]["facility_level_end_of_run"]>;
}

function toBarData(snapshot: FacilitySnapshot, t: (key: string) => string) {
  return [
    { level: t("facilityLevels.home"), value: snapshot.home },
    { level: t("facilityLevels.l23"), value: snapshot.l23 },
    { level: t("facilityLevels.l4"), value: snapshot.l4 },
    { level: t("facilityLevels.l5"), value: snapshot.l5 },
  ];
}

function MiniBarChart({
  title,
  data,
  chartId,
  filename,
}: {
  title: string;
  data: Array<{ level: string; value: number }>;
  chartId: string;
  filename: string;
}) {
  const { t } = useLocale();
  const isMobile = useIsMobile();
  const chartLayout = getChartLayout(isMobile);

  return (
    <ChartPanel chartId={chartId} title={title} filename={filename} height={220} showTitle>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={chartLayout.margins}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2DAC8" />
          <XAxis dataKey="level" tick={chartLayout.tick} label={xAxisLabel(t("facilityLevels.axis"))} />
          <YAxis tick={chartLayout.tick} unit="%" label={yAxisLabel(t("charts.shareBirths"))} />
          <Tooltip {...chartTooltipProps({ valueKind: "percent" })} />
          <Bar dataKey="value" fill="#2E5F5C" />
        </BarChart>
      </ResponsiveContainer>
    </ChartPanel>
  );
}

export default function FacilityLevelProcessCharts({ bundle }: Props) {
  const { t } = useLocale();
  const intervention = {
    anc: toBarData(bundle.anc_rate.intervention, t),
    cs: toBarData(bundle.cs_rate.intervention, t),
    referral: toBarData(bundle.normal_referral.intervention, t),
  };

  return (
    <div className="grid md:grid-cols-3 gap-6">
      <MiniBarChart
        title={t("stories.ancAttendanceTitle")}
        data={intervention.anc}
        chartId="anc-by-facility"
        filename="anc-by-facility"
      />
      <MiniBarChart
        title={t("stories.csRateByFacilityTitle")}
        data={intervention.cs}
        chartId="cs-by-facility"
        filename="cs-by-facility"
      />
      <MiniBarChart
        title={t("stories.referralByFacilityTitle")}
        data={intervention.referral}
        chartId="referral-by-facility"
        filename="referral-by-facility"
      />
    </div>
  );
}
