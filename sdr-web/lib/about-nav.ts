import { TranslateFn } from "./i18n";

/** Only allow same-origin relative paths (prevents open redirects). */
export function safeReturnPath(raw: string | null | undefined): string | null {
  if (!raw) return null;
  try {
    const path = decodeURIComponent(raw);
    if (!path.startsWith("/") || path.startsWith("//")) return null;
    if (path.startsWith("/about")) return null;
    return path;
  } catch {
    return null;
  }
}

export function getCurrentReturnPath(pathname: string, search: string): string {
  if (pathname === "/about") return "";
  return pathname + (search ? `?${search}` : "");
}

export function aboutHref(returnTo?: string | null): string {
  const safe = safeReturnPath(returnTo);
  if (!safe) return "/about";
  return `/about?returnTo=${encodeURIComponent(safe)}`;
}

export function aboutBackLabel(returnTo: string | null, t: TranslateFn): string {
  if (!returnTo) return t("about.backToStart");
  if (returnTo.startsWith("/compare")) return t("about.backToCompare");
  if (returnTo.startsWith("/design")) return t("about.backToDesign");
  if (returnTo.startsWith("/results")) return t("about.backToResults");
  return t("about.backToPrevious");
}
