import { KENYA_COUNTY_PATHS } from "@/lib/data/kenya-county-paths";

export interface CountyMeta {
  id: string;
  name: string;
  calibrated: boolean;
  population?: number;
  available?: string;
}

export type SupportedCountyId = "kakamega" | "kisii" | "makueni" | "mombasa";

export const COUNTY_STORAGE_KEY = "sdr_county";
export const DEFAULT_COUNTY_ID: SupportedCountyId = "kakamega";

/** Counties with calibrated model parameters (matches API meta / workbook). */
export const COUNTIES: CountyMeta[] = [
  { id: "kakamega", name: "Kakamega", calibrated: true, population: 1_867_283 },
  { id: "kisii", name: "Kisii", calibrated: true, population: 1_266_860 },
  { id: "makueni", name: "Makueni", calibrated: true, population: 987_653 },
  { id: "mombasa", name: "Mombasa", calibrated: true, population: 1_208_333 },
];

export function getCountyById(id: string): CountyMeta | undefined {
  return COUNTIES.find((c) => c.id === id);
}

export function isSupportedCountyId(id: string): id is SupportedCountyId {
  return COUNTIES.some((c) => c.id === id);
}

export function countyDisplayName(id: string): string {
  const c = getCountyById(id);
  if (c) return `${c.name} County`;
  const fromMap = id
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
  return `${fromMap} County`;
}

export function getCountyLabel(id: string): string {
  const meta = getCountyById(id);
  if (meta) return meta.name;
  const path = KENYA_COUNTY_PATHS.find((p) => p.id === id);
  return path?.name ?? id;
}

export function isCountySelectable(id: string): boolean {
  return getCountyById(id)?.calibrated === true;
}

export function formatCountyPopulation(population?: number): string {
  if (!population) return "";
  return (population / 1_000_000).toFixed(2);
}

export function getStoredCountyId(): SupportedCountyId {
  if (typeof window === "undefined") return DEFAULT_COUNTY_ID;
  const raw = localStorage.getItem(COUNTY_STORAGE_KEY);
  return raw && isCountySelectable(raw) && isSupportedCountyId(raw) ? raw : DEFAULT_COUNTY_ID;
}

export function storeCountyId(id: string): void {
  if (typeof window === "undefined") return;
  if (isCountySelectable(id) && isSupportedCountyId(id)) {
    localStorage.setItem(COUNTY_STORAGE_KEY, id);
  }
}
