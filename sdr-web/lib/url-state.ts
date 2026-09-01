import { mergeScenario } from "./interventions";
import { DEFAULT_SCENARIO, Scenario, SupportedCountyId } from "./scenarios";

export function scenarioToURLParams(scenario: Scenario): string {
  return JSON.stringify(scenario);
}

export function scenarioFromURLParams(encoded: string | null): Scenario | null {
  if (!encoded) return null;

  const tryParse = (raw: string): Scenario | null => {
    try {
      const parsed = JSON.parse(raw) as Partial<Scenario>;
      return mergeScenario(DEFAULT_SCENARIO, parsed);
    } catch {
      return null;
    }
  };

  const direct = tryParse(encoded);
  if (direct) return direct;

  try {
    return tryParse(decodeURIComponent(encoded));
  } catch {
    return null;
  }
}

export function scenarioToSearchParams(scenario: Scenario): URLSearchParams {
  const params = new URLSearchParams();
  params.set("s", scenarioToURLParams(scenario));
  return params;
}

/** Apply the user's county choice to a scenario and build a Design page href. */
export function designHref(countyId: SupportedCountyId, scenario?: Scenario | null): string {
  const merged = mergeScenario(DEFAULT_SCENARIO, {
    ...(scenario ?? DEFAULT_SCENARIO),
    county: countyId,
  });
  return `/design?${scenarioToSearchParams(merged).toString()}`;
}
