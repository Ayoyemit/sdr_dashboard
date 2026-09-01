"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
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
import ChartFootnote from "@/components/results/ChartFootnote";
import DeathsByCauseChart from "@/components/results/DeathsByCauseChart";
import FacilityLevelProcessCharts from "@/components/results/FacilityLevelProcessCharts";
import FacilityMortalityChart from "@/components/results/FacilityMortalityChart";
import { useLocale } from "@/components/i18n/LocaleProvider";
import StoryIngredients from "@/components/results/StoryIngredients";
import IndicatorStoryCharts from "@/components/results/IndicatorStoryCharts";
import { shouldShowStory } from "@/lib/indicators";
import { isCostStoryAvailable } from "@/lib/results-summary";
import {
  chartTooltipProps,
  getChartLayout,
  xAxisLabel,
  yAxisLabel,
} from "@/lib/chart-labels";
import { useIsMobile } from "@/lib/use-breakpoint";
import { ScenarioResult, SupportedCountyId } from "@/lib/scenarios";

interface Props {
  result: ScenarioResult;
  selectedIndicators: Set<string>;
  countyId: SupportedCountyId;
}

export default function ResultsStories({ result, selectedIndicators, countyId }: Props) {
  const { t } = useLocale();
  const isMobile = useIsMobile();
  const chartLayout = getChartLayout(isMobile);
  const { summary, timeseries, cost_breakdown, deaths_by_cause } = result;
  const showCostStory = isCostStoryAvailable(countyId);

  const ciLower = timeseries.maternal_mortality_rate.ci_lower;
  const ciUpper = timeseries.maternal_mortality_rate.ci_upper;
  const showCi = !!(ciLower && ciUpper && ciLower.length === timeseries.months.length);

  const mmData = timeseries.months.map((m, i) => ({
    month: m,
    baseline: timeseries.maternal_mortality_rate.baseline[i],
    intervention: timeseries.maternal_mortality_rate.intervention[i],
    ...(showCi ? { ciBand: [ciLower![i], ciUpper![i]] as [number, number] } : {}),
  }));

  const deliveryData = timeseries.months.map((m, i) => ({
    month: m,
    l4: timeseries.delivery_location.intervention.l4[i],
    l5: timeseries.delivery_location.intervention.l5[i],
    home: timeseries.delivery_location.intervention.home[i],
    l23: timeseries.delivery_location.intervention.l23[i],
  }));

  const showStory01 = shouldShowStory("story01", selectedIndicators);
  const showStory02 = shouldShowStory("story02", selectedIndicators);
  const showStory03 = shouldShowStory("story03", selectedIndicators);
  const showStory04 = shouldShowStory("story04", selectedIndicators);
  const facilityMortality = timeseries.mortality_by_facility_level;
  const facilityLevelEnd = timeseries.facility_level_end_of_run;

  const noStories = !showStory01 && !showStory02 && !showStory03 && !showStory04;

  return (
    <div className="space-y-12">
      {noStories && (
        <div className="bg-paper-deep border border-border rounded-lg p-8 text-center text-ink-muted">
          {t("stories.noIndicators")}
        </div>
      )}

      {showStory01 && (
        <section className="bg-card border border-border rounded-xl p-4 md:p-8">
          <div className="text-[11px] uppercase tracking-widest text-ink-muted mb-2">
            {t("stories.story01")}
          </div>
          <h2 className="font-display text-2xl mb-2">{t("stories.healthOutcomes")}</h2>
          <StoryIngredients story="story01" selected={selectedIndicators} />
          {facilityMortality ? (
            <FacilityMortalityChart
              months={timeseries.months}
              series={facilityMortality.intervention}
            />
          ) : null}
          <ChartPanel
            chartId="maternal-mortality"
            title={t("charts.mmrTitle")}
            filename="maternal-mortality"
            height={340}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mmData} margin={chartLayout.marginsWithLegend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2DAC8" />
                <XAxis dataKey="month" tick={chartLayout.tick} label={xAxisLabel(t("charts.month"))} />
                <YAxis tick={chartLayout.tick} label={yAxisLabel(t("charts.mmr"))} />
                <Tooltip {...chartTooltipProps({ valueKind: "mmr", labelPrefix: t("charts.month") })} />
                <Legend {...chartLayout.legend} />
                {showCi && (
                  <Area
                    type="monotone"
                    dataKey="ciBand"
                    stroke="none"
                    fill="#2E5F5C"
                    fillOpacity={0.14}
                    name="95% interval (intervention)"
                    legendType="rect"
                    isAnimationActive={false}
                  />
                )}
                <Line type="monotone" dataKey="baseline" stroke="#9C9082" name="Baseline MMR" dot={false} />
                <Line
                  type="monotone"
                  dataKey="intervention"
                  stroke="#2E5F5C"
                  name="Intervention MMR"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartPanel>
          <ChartFootnote>
            {showCi
              ? t("stories.footnoteMmrCi", { runs: result.meta.n_runs })
              : t("stories.footnoteMmrQuick")}
          </ChartFootnote>
          <DeathsByCauseChart deathsByCause={deaths_by_cause} />
        </section>
      )}

      {showStory02 && (
        <section className="bg-card border border-border rounded-xl p-4 md:p-8">
          <div className="text-[11px] uppercase tracking-widest text-ink-muted mb-2">
            {t("stories.story02")}
          </div>
          <h2 className="font-display text-2xl mb-2">{t("stories.delivery")}</h2>
          <StoryIngredients story="story02" selected={selectedIndicators} />
          <ChartPanel
            chartId="delivery-location"
            title={t("charts.deliveryTitle")}
            filename="delivery-location"
            height={340}
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={deliveryData} margin={chartLayout.marginsWithLegend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2DAC8" />
                <XAxis dataKey="month" tick={chartLayout.tick} label={xAxisLabel(t("charts.month"))} />
                <YAxis tick={chartLayout.tick} unit="%" label={yAxisLabel(t("charts.shareBirths"))} />
                <Tooltip {...chartTooltipProps({ valueKind: "percent", labelPrefix: t("charts.month") })} />
                <Legend {...chartLayout.legend} />
                <Area type="monotone" dataKey="l4" stackId="1" stroke="#2E5F5C" fill="#2E5F5C" name="L4" />
                <Area type="monotone" dataKey="l5" stackId="1" stroke="#B5471F" fill="#B5471F" name="L5" />
                <Area type="monotone" dataKey="l23" stackId="1" stroke="#7E7464" fill="#7E7464" name="L2/3" />
                <Area type="monotone" dataKey="home" stackId="1" stroke="#9C9082" fill="#9C9082" name="Home" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartPanel>
          <ChartFootnote>{t("stories.footnoteDelivery")}</ChartFootnote>
        </section>
      )}

      {showStory03 && (
        <section className="bg-card border border-border rounded-xl p-4 md:p-8">
          <div className="text-[11px] uppercase tracking-widest text-ink-muted mb-2">
            {t("stories.story03")}
          </div>
          <h2 className="font-display text-2xl mb-2">{t("stories.process")}</h2>
          <StoryIngredients story="story03" selected={selectedIndicators} />
          {facilityLevelEnd ? (
            <FacilityLevelProcessCharts bundle={facilityLevelEnd} />
          ) : (
            <IndicatorStoryCharts
              result={result}
              indicatorIds={["anc_coverage", "anc_rate", "cs_rate", "normal_referral"]}
              selected={selectedIndicators}
            />
          )}
        </section>
      )}

      {showStory04 && (
        <section className="bg-card border border-border rounded-xl p-4 md:p-8">
          <div className="text-[11px] uppercase tracking-widest text-ink-muted mb-2">
            {t("stories.story04")}
          </div>
          <h2 className="font-display text-2xl mb-2 editorial-underline inline">
            {t("stories.interventionCost")}
          </h2>
          <StoryIngredients story="story04" selected={selectedIndicators} />
          {!showCostStory ? (
            <div className="bg-paper-deep border border-border-soft rounded-lg px-6 py-8 text-center text-sm text-ink-muted">
              {t("stories.kakamegaOnly")}
            </div>
          ) : (
            <>
              <div className="grid md:grid-cols-2 gap-8">
                <div>
                  <div className="font-display text-3xl sm:text-5xl text-accent num mb-2">
                    $
                    {summary.cumulative_cost_usd.toLocaleString(undefined, {
                      maximumFractionDigits: 0,
                    })}
                  </div>
                  <p className="text-sm text-ink-muted">{t("stories.totalCostCaption")}</p>
                </div>
                <ChartPanel
                  chartId="cost-breakdown"
                  title={t("charts.costBreakdown")}
                  filename="cost-breakdown"
                  height={260}
                  showTitle
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={cost_breakdown} margin={chartLayout.margins}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2DAC8" />
                      <XAxis
                        dataKey="category"
                        tick={chartLayout.tick}
                        label={xAxisLabel(t("charts.costCategory"))}
                      />
                      <YAxis tick={chartLayout.tick} label={yAxisLabel(t("charts.costUsd"))} />
                      <Tooltip {...chartTooltipProps({ valueKind: "currency" })} />
                      <Bar dataKey="amount_usd" fill="#2E5F5C" />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartPanel>
                <ChartFootnote>{t("stories.footnoteCost")}</ChartFootnote>
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}
