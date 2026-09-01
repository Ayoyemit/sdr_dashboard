"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
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
  deathsByCause: ScenarioResult["deaths_by_cause"];
}

export default function DeathsByCauseChart({ deathsByCause }: Props) {
  const { t } = useLocale();
  const isMobile = useIsMobile();
  const chartLayout = getChartLayout(isMobile);

  const data = deathsByCause.slice(0, 5).map((d) => ({
    cause: d.cause,
    baseline: Math.round(d.baseline_count),
    intervention: Math.round(d.intervention_count),
  }));

  if (data.length === 0) return null;

  return (
    <div className="mt-6">
    <ChartPanel
      chartId="deaths-by-cause"
      title={t("stories.deathsByCauseTitle")}
      filename="deaths-by-cause"
      height={280}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={chartLayout.marginsWithLegend}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2DAC8" />
          <XAxis type="number" tick={chartLayout.tick} label={xAxisLabel(t("stories.deathsCount"))} />
          <YAxis
            type="category"
            dataKey="cause"
            width={isMobile ? 100 : 140}
            tick={chartLayout.tick}
          />
          <Tooltip {...chartTooltipProps({ valueKind: "count" })} />
          <Legend {...chartLayout.legend} />
          <Bar dataKey="baseline" fill="#9C9082" name={t("indicatorCharts.baseline")} />
          <Bar dataKey="intervention" fill="#2E5F5C" name={t("indicatorCharts.intervention")} />
        </BarChart>
      </ResponsiveContainer>
    </ChartPanel>
    </div>
  );
}
