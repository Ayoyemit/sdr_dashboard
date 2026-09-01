"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import ChartPanel from "@/components/export/ChartPanel";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { chartTooltipProps, getChartLayout, xAxisLabel, yAxisLabel } from "@/lib/chart-labels";
import { useIsMobile } from "@/lib/use-breakpoint";
import { ScenarioResult } from "@/lib/scenarios";

interface Props {
  months: number[];
  series: NonNullable<ScenarioResult["timeseries"]["mortality_by_facility_level"]>["intervention"];
}

const LEVELS = [
  { key: "home" as const, color: "#9C9082", labelKey: "facilityLevels.home" },
  { key: "l23" as const, color: "#7E7464", labelKey: "facilityLevels.l23" },
  { key: "l4" as const, color: "#2E5F5C", labelKey: "facilityLevels.l4" },
  { key: "l5" as const, color: "#B5471F", labelKey: "facilityLevels.l5" },
];

export default function FacilityMortalityChart({ months, series }: Props) {
  const { t } = useLocale();
  const isMobile = useIsMobile();
  const chartLayout = getChartLayout(isMobile);

  const data = months.map((month, i) => ({
    month,
    home: series.home[i],
    l23: series.l23[i],
    l4: series.l4[i],
    l5: series.l5[i],
  }));

  return (
    <div className="mb-6">
    <ChartPanel
      chartId="mortality-by-facility"
      title={t("stories.mortalityByFacilityTitle")}
      filename="mortality-by-facility"
      height={340}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={chartLayout.marginsWithLegend}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2DAC8" />
          <XAxis dataKey="month" tick={chartLayout.tick} label={xAxisLabel(t("charts.month"))} />
          <YAxis tick={chartLayout.tick} label={yAxisLabel(t("charts.mmr"))} />
          <Tooltip {...chartTooltipProps({ valueKind: "mmr", labelPrefix: t("charts.month") })} />
          <Legend {...chartLayout.legend} />
          {LEVELS.map((level) => (
            <Line
              key={level.key}
              type="monotone"
              dataKey={level.key}
              stroke={level.color}
              name={t(level.labelKey)}
              dot={false}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartPanel>
    </div>
  );
}
