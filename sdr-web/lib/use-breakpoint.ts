"use client";

import { useEffect, useState } from "react";

export type Breakpoint = "mobile" | "tablet" | "desktop";

const QUERIES = {
  md: "(min-width: 768px)",
  lg: "(min-width: 1024px)",
} as const;

function getBreakpoint(): Breakpoint {
  if (typeof window === "undefined") return "desktop";
  if (window.matchMedia(QUERIES.lg).matches) return "desktop";
  if (window.matchMedia(QUERIES.md).matches) return "tablet";
  return "mobile";
}

export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>("desktop");

  useEffect(() => {
    const update = () => setBreakpoint(getBreakpoint());
    update();

    const md = window.matchMedia(QUERIES.md);
    const lg = window.matchMedia(QUERIES.lg);
    md.addEventListener("change", update);
    lg.addEventListener("change", update);
    return () => {
      md.removeEventListener("change", update);
      lg.removeEventListener("change", update);
    };
  }, []);

  return breakpoint;
}

export function useIsMobile(): boolean {
  const bp = useBreakpoint();
  return bp === "mobile";
}

export function useIsBelowLg(): boolean {
  const bp = useBreakpoint();
  return bp === "mobile" || bp === "tablet";
}
