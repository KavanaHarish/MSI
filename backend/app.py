import io
import csv
import json
import datetime

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from config import Config
from simulation.engine import SimulationEngine, SCENARIO_PRESETS
from ml.predictor import analyze
from db.mongo import mongo_store

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

# In-memory registry of active simulations, keyed by experiment id.
# Per-bacterium data intentionally never touches MongoDB (see db/mongo.py).
ACTIVE_SIMULATIONS = {}


def _get_engine_or_404(experiment_id):
    engine = ACTIVE_SIMULATIONS.get(experiment_id)
    if engine is None:
        return None
    return engine


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mongo_connected": mongo_store.connected})


@app.route("/api/scenarios", methods=["GET"])
def list_scenarios():
    return jsonify(SCENARIO_PRESETS)


@app.route("/api/start", methods=["POST"])
def start_experiment():
    payload = request.get_json(force=True) or {}

    scenario = payload.get("scenario")
    if scenario in SCENARIO_PRESETS:
        preset = SCENARIO_PRESETS[scenario]
        # Allow explicit overrides while defaulting to scenario mapping.
        species = payload.get("species") or preset["species"]
        grid_size = payload.get("grid_size", preset.get("grid_size", 40))
        initial_population = payload.get("initial_population", preset.get("initial_population", 120))
        mutation_rate = payload.get("mutation_rate", preset.get("mutation_rate", 0.05))
        mutation_strength = payload.get("mutation_strength", preset.get("mutation_strength", 0.1))
        antibiotic_level = payload.get("antibiotic_level", preset.get("antibiotic_level", 0.5))
        growth_rate = payload.get("growth_rate", preset.get("growth_rate", 0.3))
        hgt_rate = payload.get("hgt_rate", preset.get("hgt_rate", 0.02))
        simulation_speed = payload.get("simulation_speed", 1.0)
    else:
        scenario = None
        species = payload.get("species", "ecoli")
        grid_size = payload.get("grid_size", 40)
        initial_population = payload.get("initial_population", 120)
        mutation_rate = payload.get("mutation_rate", 0.05)
        mutation_strength = payload.get("mutation_strength", 0.1)
        antibiotic_level = payload.get("antibiotic_level", 0.5)
        growth_rate = payload.get("growth_rate", 0.3)
        simulation_speed = payload.get("simulation_speed", 1.0)
        hgt_rate = payload.get("hgt_rate", 0.02)

    engine = SimulationEngine(
        species=species,
        grid_size=grid_size,
        initial_population=initial_population,
        mutation_rate=mutation_rate,
        mutation_strength=mutation_strength,
        antibiotic_level=antibiotic_level,
        growth_rate=growth_rate,
        simulation_speed=simulation_speed,
        hgt_rate=hgt_rate,
        scenario=scenario,
    )
    engine.running = True
    ACTIVE_SIMULATIONS[engine.id] = engine

    mongo_store.save_experiment(
        engine.id,
        {
            "config": engine.config_metadata(),
            "started_at": datetime.datetime.utcnow(),
            "status": "running",
        },
    )

    return jsonify(engine.get_state())


@app.route("/api/step", methods=["POST"])
def step_experiment():
    payload = request.get_json(force=True) or {}
    experiment_id = payload.get("experiment_id")
    steps = int(payload.get("steps", 1))

    engine = _get_engine_or_404(experiment_id)
    if engine is None:
        return jsonify({"error": "experiment not found"}), 404

    last_snapshot = None
    for _ in range(max(1, steps)):
        last_snapshot = engine.step()
        mongo_store.save_snapshot(experiment_id, last_snapshot)

    return jsonify(engine.get_state())


@app.route("/api/state", methods=["GET"])
def get_state():
    experiment_id = request.args.get("experiment_id")
    engine = _get_engine_or_404(experiment_id)
    if engine is None:
        return jsonify({"error": "experiment not found"}), 404
    return jsonify(engine.get_state())


@app.route("/api/prediction", methods=["GET"])
def get_prediction():
    experiment_id = request.args.get("experiment_id")
    engine = _get_engine_or_404(experiment_id)
    if engine is None:
        return jsonify({"error": "experiment not found"}), 404
    return jsonify(analyze(engine.history))


@app.route("/api/history", methods=["GET"])
def get_history():
    experiment_id = request.args.get("experiment_id")
    engine = _get_engine_or_404(experiment_id)
    if engine is not None:
        return jsonify(engine.history)
    # fall back to persisted history if the in-memory engine has been cleared
    return jsonify(mongo_store.get_history(experiment_id))


@app.route("/api/reset", methods=["POST"])
def reset_experiment():
    payload = request.get_json(force=True) or {}
    experiment_id = payload.get("experiment_id")
    if experiment_id in ACTIVE_SIMULATIONS:
        del ACTIVE_SIMULATIONS[experiment_id]
    return jsonify({"status": "reset"})


@app.route('/api/treat', methods=['POST'])
def apply_treatment():
    data = request.get_json(force=True) or {}
    experiment_id = data.get("experiment_id")
    
    engine = _get_engine_or_404(experiment_id)
    if engine is None:
        return jsonify({"error": "experiment not found"}), 404
        
    intensity = data.get('intensity', 0.8)
    x = data.get('x', None)
    y = data.get('y', None)
    drug = data.get('drug_name', 'Secondary Antibiotic')
    
    state = engine.apply_treatment(intensity, x, y, drug)
    return jsonify(state)


@app.route("/api/report", methods=["GET"])
def get_report():
    experiment_id = request.args.get("experiment_id")
    fmt = request.args.get("format", "json")
    engine = _get_engine_or_404(experiment_id)
    if engine is None:
        return jsonify({"error": "experiment not found"}), 404

    prediction = analyze(engine.history)
    report = {
        "experiment_id": experiment_id,
        "config": engine.config_metadata(),
        "final_generation": engine.generation,
        "history": engine.history,
        "prediction": prediction,
        "generated_at": datetime.datetime.utcnow().isoformat(),
    }
    mongo_store.save_report(experiment_id, report)

    if fmt == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=list(engine.history[0].keys()) if engine.history else [],
        )
        writer.writeheader()
        for row in engine.history:
            writer.writerow(row)
        mem = io.BytesIO(buffer.getvalue().encode("utf-8"))
        return send_file(
            mem,
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"experiment_{experiment_id}.csv",
        )

    if fmt == "json":
        mem = io.BytesIO(json.dumps(report, indent=2, default=str).encode("utf-8"))
        return send_file(
            mem,
            mimetype="application/json",
            as_attachment=True,
            download_name=f"experiment_{experiment_id}.json",
        )

    return jsonify(report)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)