"use client";

import { useLocale } from "@/components/i18n/LocaleProvider";
import { countyDisplayName } from "@/lib/counties";
import { listActiveInterventions, INTERVENTION_LIBRARY } from "@/lib/interventions";
import { Scenario } from "@/lib/scenarios";

interface Props {
  scenario: Scenario;
}

export default function ScenarioAssumptionsBanner({ scenario }: Props) {
  const { t } = useLocale();
  const active = listActiveInterventions(scenario);
  const labels = active
    .map((id) => INTERVENTION_LIBRARY.find((item) => item.id === id)?.name ?? id)
    .join(" · ");

  return (
    <div className="mb-6 rounded-lg border border-border bg-card px-4 py-3 text-sm">
      <strong className="text-ink block text-xs uppercase tracking-wider mb-1">
        {t("assumptions.title")}
      </strong>
      <p className="text-ink-soft leading-relaxed mb-2">{t("assumptions.body")}</p>
      <ul className="text-xs text-ink-muted space-y-1">
        <li>
          {t("assumptions.county", { county: countyDisplayName(scenario.county) })}
        </li>
        <li>
          {t("assumptions.horizon", {
            years: scenario.run.implementation_years + scenario.run.maintenance_years,
            impl: scenario.run.implementation_years,
            maint: scenario.run.maintenance_years,
            mode: scenario.run.mode,
          })}
        </li>
        <li>
          {active.length > 0
            ? t("assumptions.interventions", { list: labels })
            : t("assumptions.baselineOnly")}
        </li>
      </ul>
    </div>
  );
}
