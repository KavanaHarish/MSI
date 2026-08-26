"""
ML Analysis Layer.

IMPORTANT: this module never touches the simulation itself. It only reads
the generation-by-generation history the SimulationEngine has already
produced and fits lightweight models to forecast where resistance is
heading. This keeps "what happens" (engine) cleanly separated from
"what we predict will happen" (ML), as required by the project spec.

Modelling approach:
  - A RandomForestRegressor learns the per-generation *change* in average
    resistance from the historical feature log (generation, population,
    deaths, mutations, survival rate, hotspots, resistant fraction).
  - The forecast then recurses forward 20 generations by advancing the
    generation feature while carrying the latest environmental state.
  - The confidence score is computed dynamically from the fit R^2 and the
    residual scatter: chaotic, erratic histories score lower.
  - The risk zone factors real population density, mutation velocity and
    death rate in addition to hotspot and resistance-slope signals.
"""
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

MIN_POINTS_FOR_PREDICTION = 6
FORECAST_HORIZON = 20
RECENT_WINDOW = 10
DOMINANCE_THRESHOLD = 0.7


def _feature_vector(h):
    """State vector for a single historical snapshot."""
    return np.array(
        [
            float(h["generation"]),
            float(h["population"]),
            float(h["deaths"]),
            float(h["mutations"]),
            float(h["survival_rate"]),
            float(h["hotspot_count"]),
            float(h["resistant_fraction"]),
        ]
    )


def _analyze(history):
    n = len(history)
    last = history[-1]
    last_gen = int(last["generation"])

    # ---- Train a random forest on historical resistance dynamics ---------
    # X = state features at generation g; y = average resistance at g+1.
    X = np.array([_feature_vector(history[g]) for g in range(n - 1)])
    y = np.array([history[g + 1]["avg_resistance"] for g in range(n - 1)])

    model = RandomForestRegressor(n_estimators=60, max_depth=6, random_state=0)
    model.fit(X, y)

    # ---- Dynamic confidence: R^2 penalised by residual scatter -----------
    in_sample = model.predict(X)
    residuals = y - in_sample
    r2 = float(r2_score(y, in_sample))
    relative_scatter = float(np.std(residuals) / (np.std(y) + 1e-9))
    confidence = int(
        round(max(0.0, min(1.0, r2)) * (1.0 - min(0.6, relative_scatter)) * 100)
    )

    # ---- Recursive 20-generation forecast ---------------------------------
    state = _feature_vector(last)
    future_gens = np.arange(last_gen + 1, last_gen + FORECAST_HORIZON + 1)
    future_resistance = []
    future_res = float(last["avg_resistance"])
    for g in future_gens:
        state[0] = float(g)
        state[6] = float(np.clip((future_res - 0.5) / 0.5, 0.0, 1.0))
        future_res = float(np.clip(float(model.predict(state.reshape(1, -1))[0]), 0.0, 1.0))
        future_resistance.append(future_res)
    future_resistance = np.array(future_resistance)

    # ---- Estimated generation of dominance ---------------------------------
    dominant_gen = None
    for gen, val in zip(future_gens, future_resistance):
        if val >= DOMINANCE_THRESHOLD:
            dominant_gen = int(gen)
            break

    # ---- Live-state risk metrics -------------------------------------------
    window = min(RECENT_WINDOW, n)
    generations = np.array([h["generation"] for h in history])
    resistance_series = np.array([h["avg_resistance"] for h in history])
    population_series = np.array([h["population"] for h in history])

    res_slope = float(np.polyfit(generations[-window:], resistance_series[-window:], 1)[0])
    pop_slope = float(np.polyfit(generations[-window:], population_series[-window:], 1)[0])

    recent = history[-window:]
    avg_hotspots = float(np.mean([h["hotspot_count"] for h in recent]))
    density = float(last["population"] / max(1.0, float(population_series.max())))
    mutation_velocity = float(np.mean([h["mutations"] for h in recent]))
    avg_pop = float(np.mean([h["population"] for h in recent]))
    death_rate = float(np.mean([h["deaths"] for h in recent]) / max(1.0, avg_pop))

    hotspot_risk = min(25.0, avg_hotspots * 8.0)
    slope_risk = min(30.0, max(0.0, res_slope) * 2500.0)
    density_risk = min(15.0, density * 20.0)
    mutation_risk = min(15.0, mutation_velocity * 20.0)
    death_risk = min(15.0, death_rate * 50.0)
    risk_score = int(round(hotspot_risk + slope_risk + density_risk + mutation_risk + death_risk))
    high_risk = risk_score >= 50

    # ---- Antibiotic effectiveness --------------------------------------------
    effectiveness = max(0.0, min(1.0, 1.0 - res_slope * 5.0))

    # ---- Plain-language recommendation ---------------------------------------
    rec = []
    if res_slope > 0.01:
        rec.append("Mutation-driven resistance is accelerating.")
    if dominant_gen:
        rec.append(
            f"Resistant colony dominance projected around generation {dominant_gen}."
        )
    if avg_hotspots > 2:
        rec.append("Persistent resistance hotspots detected in the grid.")
    if density > 0.7:
        rec.append("The dish is densely populated — conjugation spreads resistance faster.")
    if mutation_velocity > 0.5:
        rec.append("Elevated mutation velocity is feeding new resistant variants.")
    if death_rate > 0.2:
        rec.append("High death rate is concentrating survivors under strong selection pressure.")
    if effectiveness < 0.4:
        rec.append(
            "Current antibiotic level is losing effectiveness — consider increasing dosage "
            "or switching treatment strategy."
        )
    if not rec:
        rec.append("Population remains largely susceptible; current antibiotic level appears effective.")

    return {
        "ready": True,
        "model_used": "Random Forest (resistance dynamics)",
        "future_resistance": [round(float(v), 4) for v in future_resistance],
        "future_generations": [int(g) for g in future_gens],
        "estimated_dominant_generation": dominant_gen,
        "population_trend": "increasing" if pop_slope > 0 else "decreasing",
        "population_trend_slope": round(pop_slope, 2),
        "high_risk_zone": bool(high_risk),
        "risk_score": risk_score,
        "risk_factors": {
            "hotspots": round(hotspot_risk, 1),
            "resistance_slope": round(slope_risk, 1),
            "population_density": round(density_risk, 1),
            "mutation_velocity": round(mutation_risk, 1),
            "death_rate": round(death_risk, 1),
        },
        "antibiotic_effectiveness": round(effectiveness * 100, 1),
        "confidence_score": confidence,
        "recommendation": " ".join(rec),
    }


def analyze(history):
    """
    history: list of per-generation snapshot dicts from SimulationEngine.
    Returns a dict describing predicted future resistance trajectory,
    estimated generation of dominance, hotspot risk, antibiotic
    effectiveness, dynamic confidence, and a plain-language recommendation.
    """
    if len(history) < MIN_POINTS_FOR_PREDICTION:
        return {
            "ready": False,
            "message": "Collecting data — need a few more generations before predictions stabilize.",
        }
    try:
        return _analyze(history)
    except Exception:
        return {
            "ready": False,
            "message": "Prediction engine could not fit the current history — try running more generations.",
        }
