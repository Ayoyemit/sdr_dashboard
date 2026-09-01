import { Scenario } from "./scenarios";

/** Fields that do not affect simulation output — excluded from cache keys. */
const FINGERPRINT_IGNORE = new Set(["name", "ui_levels"]);

function fingerprintPayload(scenario: Scenario): Record<string, unknown> {
  const payload = { ...scenario } as Record<string, unknown>;
  FINGERPRINT_IGNORE.forEach((key) => {
    delete payload[key];
  });
  return payload;
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(",")}]`;
  }
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify(obj[k])}`).join(",")}}`;
}

/** Matches API fingerprinting shape (simulation inputs only). */
export function scenarioFingerprint(scenario: Scenario): string {
  const raw = stableStringify(fingerprintPayload(scenario));
  let hash = 0;
  for (let i = 0; i < raw.length; i += 1) {
    hash = (hash << 5) - hash + raw.charCodeAt(i);
    hash |= 0;
  }
  return `fp_${Math.abs(hash).toString(16)}`;
}
