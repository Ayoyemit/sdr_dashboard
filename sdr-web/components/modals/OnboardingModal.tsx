"use client";

import { useEffect, useState } from "react";

export default function OnboardingModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem("sdr-onboarding-seen")) {
      setOpen(true);
    }
  }, []);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-ink/50 p-0 sm:p-4 safe-bottom">
      <div className="bg-card border border-border rounded-t-xl sm:rounded-xl p-6 sm:p-8 max-w-lg w-full shadow-2xl max-h-[90dvh] overflow-y-auto">
        <h2 className="font-display text-xl sm:text-2xl mb-3">Welcome to the Decision Tool</h2>
        <p className="text-ink-soft text-sm leading-relaxed mb-4">
          Explore maternal health scenarios across calibrated Kenya counties. Pick a preset, adjust intensity
          in plain language, and run a simulation to see projected outcomes and cost-effectiveness.
        </p>
        <ol className="text-sm text-ink-soft space-y-2 mb-6 list-decimal list-inside">
          <li>Choose a starting preset or build your own scenario</li>
          <li>Configure HSS, treatments, and community interventions</li>
          <li>Run the simulation and explore story-driven results</li>
        </ol>
        <button
          type="button"
          onClick={() => {
            localStorage.setItem("sdr-onboarding-seen", "1");
            setOpen(false);
          }}
          className="w-full min-h-[44px] py-3 bg-ink text-paper rounded-md font-medium"
        >
          Get started
        </button>
      </div>
    </div>
  );
}
