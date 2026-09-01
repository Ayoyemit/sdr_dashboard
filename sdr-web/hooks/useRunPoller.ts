"use client";

import { useEffect, useRef, useState } from "react";
import { pollRun } from "@/lib/api";
import { finalizeCompletedRun } from "@/lib/geography-run";
import { Scenario, ScenarioResult } from "@/lib/scenarios";

interface RunPollerState {
  loading: boolean;
  scenario: Scenario | null;
  result: ScenarioResult | null;
  error: string | null;
  estimatedSecondsRemaining: number | null;
  pollCount: number;
}

export function useRunPoller(runId: string | null, initialScenario?: Scenario | null): RunPollerState {
  const [loading, setLoading] = useState(true);
  const [scenario, setScenario] = useState<Scenario | null>(initialScenario ?? null);
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [estimatedSecondsRemaining, setEstimatedSecondsRemaining] = useState<number | null>(null);
  const [pollCount, setPollCount] = useState(0);
  const attemptsRef = useRef(0);

  useEffect(() => {
    if (!runId) {
      setLoading(false);
      setError("No run ID found. Please run a simulation from the Design page.");
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    attemptsRef.current = 0;

    const scheduleNext = () => {
      const delay = attemptsRef.current < 30 ? 1000 : 2000;
      timer = setTimeout(() => {
        void pollOnce();
      }, delay);
    };

    const pollOnce = async () => {
      try {
        const response = await pollRun(runId);
        if (cancelled) return;

        attemptsRef.current += 1;
        setPollCount(attemptsRef.current);
        setEstimatedSecondsRemaining(response.estimated_seconds_remaining ?? null);
        setScenario(response.scenario);

        if (response.status === "complete" && response.result) {
          setResult(response.result);
          finalizeCompletedRun(runId, response.scenario, response.result);
          setError(null);
          setLoading(false);
          return;
        }

        if (response.status === "failed") {
          setError(response.error_message || "Simulation failed. Please try again.");
          setLoading(false);
          return;
        }

        scheduleNext();
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Failed to load results");
        setLoading(false);
      }
    };

    setLoading(true);
    setError(null);
    setResult(null);
    setPollCount(0);
    void pollOnce();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [runId]);

  return {
    loading,
    scenario,
    result,
    error,
    estimatedSecondsRemaining,
    pollCount,
  };
}
