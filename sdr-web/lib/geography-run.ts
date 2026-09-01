import { pollRun, startScenarioRun } from "./api";
import { saveLastRun } from "./last-run-storage";
import { scenarioFingerprint } from "./scenario-fingerprint";
import { Scenario, SupportedCountyId } from "./scenarios";
import { scenarioToSearchParams } from "./url-state";

const GEO_RUN_INDEX_KEY = "sdr_geo_run_index";

interface GeoRunIndexEntry {
  fingerprint: string;
  runId: string;
  county: SupportedCountyId;
  savedAt: number;
}

function readGeoRunIndex(): GeoRunIndexEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = sessionStorage.getItem(GEO_RUN_INDEX_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as GeoRunIndexEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeGeoRunIndex(entries: GeoRunIndexEntry[]): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(GEO_RUN_INDEX_KEY, JSON.stringify(entries.slice(-24)));
}

export function rememberGeoRun(scenario: Scenario, runId: string): void {
  const fingerprint = scenarioFingerprint(scenario);
  const entries = readGeoRunIndex().filter((e) => e.fingerprint !== fingerprint);
  entries.push({
    fingerprint,
    runId,
    county: scenario.county,
    savedAt: Date.now(),
  });
  writeGeoRunIndex(entries);
}

export function forgetGeoRun(scenario: Scenario): void {
  const fingerprint = scenarioFingerprint(scenario);
  writeGeoRunIndex(readGeoRunIndex().filter((e) => e.fingerprint !== fingerprint));
}

export function scenarioForCounty(scenario: Scenario, county: SupportedCountyId): Scenario {
  return { ...scenario, county };
}

export function resultsHrefForRun(scenario: Scenario, runId: string): string {
  const params = scenarioToSearchParams(scenario);
  params.set("run_id", runId);
  return `/results?${params.toString()}`;
}

/**
 * Always ask the API (server fingerprint cache is authoritative).
 * Returns immediately with pending or complete.
 */
export async function startRunForGeography(scenario: Scenario): Promise<{
  runId: string;
  scenario: Scenario;
  fromCache: boolean;
}> {
  const response = await startScenarioRun(scenario);
  if (response.status === "failed") {
    forgetGeoRun(scenario);
    throw new Error(response.error_message || "Simulation failed");
  }
  if (response.status === "complete" && response.result) {
    saveLastRun(response.run_id, scenario, response.result);
    rememberGeoRun(scenario, response.run_id);
    return { runId: response.run_id, scenario, fromCache: true };
  }

  return { runId: response.run_id, scenario, fromCache: false };
}

export function finalizeCompletedRun(
  runId: string,
  scenario: Scenario,
  result: NonNullable<import("./scenarios").RunResponse["result"]>
): void {
  saveLastRun(runId, scenario, result);
  rememberGeoRun(scenario, runId);
}
