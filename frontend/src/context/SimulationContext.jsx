import { createContext, useContext, useRef, useState, useCallback, useEffect } from "react";

import {
  startExperiment,
  stepExperiment,
  getPrediction,
  getHistory,
  resetExperiment,
  treatExperiment,
} from "../api/client.js";

const SimulationContext = createContext(null);

const DEFAULT_CONFIG = {
  scenario: "",
  species: "",
  antibiotic: "",
  grid_size: 40,
  initial_population: 120,
  mutation_rate: 0.05,
  mutation_strength: 0.1,
  antibiotic_level: 0.5,
  growth_rate: 0.3,
  simulation_speed: 1.0,
  hgt_rate: 0.02,
};

export function SimulationProvider({ children }) {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [experimentId, setExperimentId] = useState(null);
  const [state, setState] = useState(null); // latest engine state (cells, field, stats)
  const [history, setHistory] = useState([]);
  const [prediction, setPrediction] = useState({ ready: false });
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [startError, setStartError] = useState(null);
  const timeoutRef = useRef(null);
  const runningRef = useRef(false);
  const tickInFlightRef = useRef(false);
  const sessionRef = useRef(0);
  const experimentIdRef = useRef(null);
  const speedRef = useRef(DEFAULT_CONFIG.simulation_speed);

  const getSpeedMs = useCallback(
    () => Math.max(120, 700 / (speedRef.current || 1)),
    []
  );

  useEffect(() => {
    speedRef.current = config.simulation_speed || 1;
  }, [config.simulation_speed]);

  const clearTimer = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const updateConfig = useCallback((patch) => {
    setConfig((prev) => ({ ...prev, ...patch }));
    setStartError(null);
  }, []);

  const scheduleNext = useCallback((id, session) => {
    if (!runningRef.current || session !== sessionRef.current || id !== experimentIdRef.current) return;
    clearTimer();
    timeoutRef.current = setTimeout(() => {
      void runTick(id, session);
    }, getSpeedMs());
  }, [clearTimer, getSpeedMs]);

  const runTick = useCallback(async (id, session) => {
    if (!runningRef.current || session !== sessionRef.current || id !== experimentIdRef.current) return;
    if (tickInFlightRef.current) {
      scheduleNext(id, session);
      return;
    }
    tickInFlightRef.current = true;
    try {
      const newState = await stepExperiment(id, 1);
      if (!runningRef.current || session !== sessionRef.current || id !== experimentIdRef.current) return;
      setState(newState);
      setHistory((prev) => [...prev, newState.stats].slice(-200));
      if (newState.stats?.generation % 3 === 0) {
        getPrediction(id)
          .then((pred) => {
            if (session === sessionRef.current && id === experimentIdRef.current) setPrediction(pred);
          })
          .catch(() => {});
      }
    } catch (_) {
      // keep running state; next tick will retry
    } finally {
      tickInFlightRef.current = false;
      if (runningRef.current && session === sessionRef.current && id === experimentIdRef.current) {
        scheduleNext(id, session);
      }
    }
  }, [scheduleNext]);

  const start = useCallback(async () => {
    setLoading(true);
    setStartError(null);
    clearTimer();
    runningRef.current = false;
    tickInFlightRef.current = false;
    sessionRef.current += 1;
    const session = sessionRef.current;
    try {
      const s = await startExperiment(config);
      experimentIdRef.current = s.id;
      setExperimentId(s.id);
      setState(s);
      setHistory([s.stats]);
      setPrediction({ ready: false });
      runningRef.current = true;
      setIsRunning(true);
      scheduleNext(s.id, session);
    } catch (err) {
      const detail = err?.response?.data?.error || err?.message || "Unknown error";
      setStartError(`Failed to start simulation. Is the backend running? (${detail})`);
      runningRef.current = false;
      setIsRunning(false);
    } finally {
      setLoading(false);
    }
  }, [config, clearTimer, scheduleNext]);

  const pause = useCallback(() => {
    runningRef.current = false;
    setIsRunning(false);
    clearTimer();
  }, [clearTimer]);

  const resume = useCallback(() => {
    if (!experimentIdRef.current || runningRef.current) return;
    runningRef.current = true;
    setIsRunning(true);
    scheduleNext(experimentIdRef.current, sessionRef.current);
  }, [scheduleNext]);

  const reset = useCallback(async () => {
    runningRef.current = false;
    setIsRunning(false);
    clearTimer();
    tickInFlightRef.current = false;
    sessionRef.current += 1;
    const id = experimentIdRef.current;
    experimentIdRef.current = null;
    if (id) {
      try { await resetExperiment(id); } catch (_) {}
    }
    setConfig(DEFAULT_CONFIG);
    setExperimentId(null);
    setState(null);
    setHistory([]);
    setPrediction({ ready: false });
  }, [clearTimer]);

  const refreshHistory = useCallback(async () => {
    const id = experimentIdRef.current;
    if (!id) return;
    const h = await getHistory(id);
    if (experimentIdRef.current === id) setHistory(h);
  }, []);

  const applyTreatment = useCallback(async (intensity = 0.8, x = null, y = null, drugName = "Secondary Antibiotic") => {
    const id = experimentIdRef.current;
    if (!id) return;
    const newState = await treatExperiment(id, intensity, x, y, drugName);
    if (experimentIdRef.current === id) setState(newState);
  }, []);

  useEffect(() => {
    return () => {
      runningRef.current = false;
      clearTimer();
      sessionRef.current += 1;
    };
  }, [clearTimer]);

  const value = {
    config,
    updateConfig,
    experimentId,
    state,
    history,
    prediction,
    isRunning,
    loading,
    startError,
    start,
    pause,
    resume,
    reset,
    refreshHistory,
    applyTreatment,
  };

  return (
    <SimulationContext.Provider value={value}>{children}</SimulationContext.Provider>
  );
}

export function useSimulation() {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error("useSimulation must be used within SimulationProvider");
  return ctx;
}
