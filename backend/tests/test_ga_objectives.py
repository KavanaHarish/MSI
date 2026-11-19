"""Quick checks: GA integration and objective-aligned features."""
from simulation.engine import SimulationEngine, SCENARIO_PRESETS


def test_ga_metrics_present():
    e = SimulationEngine(species="ecoli")
    for _ in range(12):
        snap = e.step()
    assert "ga_mean_fitness" in snap
    assert "ga_diversity" in snap
    assert snap["ga_cumulative_selection_events"] >= 0
    assert snap["ga_cumulative_crossover_events"] >= 0


def test_scenarios_mapped():
    assert "hospital_surface_mrsa" in SCENARIO_PRESETS
    assert "uti_ecoli" in SCENARIO_PRESETS
    e = SimulationEngine(scenario="uti_ecoli", species="ecoli")
    assert e.scenario == "uti_ecoli"


if __name__ == "__main__":
    test_ga_metrics_present()
    test_scenarios_mapped()
    print("ok")
