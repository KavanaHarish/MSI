# Validation & Verification Guide

This document summarizes how to answer jury questions about the Genetic Algorithm (GA), real-world applicability, and result verification for **Microbial Evolution Simulator (SIMU_NEW_VER)**.

## 1) Is the project using a Genetic Algorithm?
**Yes.** The simulator uses a genome-based GA to model evolutionary dynamics and adaptation under selective antibiotic pressure.

- GA implementation: `backend/simulation/genetic_algorithm.py`
  - Resistance genome/phenotype, fitness under local antibiotic pressure, tournament selection, crossover, and mutation (adaptive effects).
- Engine integration: `backend/simulation/engine.py`
  - GA-driven reproduction/evolution each generation (selection + crossover + mutation) alongside survival/selection dynamics and HGT.
  - GA metrics in snapshots/state/config: mean/best fitness, genome diversity, selection/crossover/mutation events (per-gen and cumulative), `ga_enabled`.
- Real-world scenario presets (mapped): `SCENARIO_PRESETS` in `backend/simulation/engine.py`
  - `hospital_surface_mrsa` — Hospital Surface Infection (MRSA)
  - `uti_ecoli` — Urinary Tract Infection (E. coli)
- API/UI exposure: `backend/app.py` (`GET /api/scenarios`, scenario-aware `POST /api/start`), `frontend/src/components/ControlPanel.jsx`, `frontend/src/components/StatPanel.jsx`.

## 2) Can it be used in the real world?
- **Appropriate use (in-silico / real-world application context):** educational and research simulation, scenario exploration (e.g. MRSA hospital surfaces, E. coli UTI), studying effects of mutation rates/antibiotic dosage/interventions, visualizing spread/heatmaps, and supporting evaluation of infection-control strategies in a safe, cost-effective way.
- **Limitations:** this is a **simulation/decision-support tool**, not a clinically validated or regulated medical device and **not a substitute for wet-lab experiments or clinical judgment**. Real-world clinical deployment would require further calibration, prospective validation against local data, and appropriate review/approval.

## 3) How to verify that simulation results are correct
Use a combination of **internal verification** and **comparison with published real-world evidence**:

1. **Internal/model verification (test cases)**
   - Confirm GA metrics and scenario mappings work as expected.
   - Test file: `backend/tests/test_ga_objectives.py`
   - Run (from `backend`, with backend on `PYTHONPATH`):
     - PowerShell: `$env:PYTHONPATH='C:\Users\kavan\OneDrive\Desktop\SIMU_NEW_VER\backend'; python tests\test_ga_objectives.py`
     - Expected: `ok`

2. **System validation runs (GA-enabled scenarios)**
   - Run mapped scenarios (MRSA hospital surface, E. coli UTI) and inspect outputs/trends (resistance, hotspots, deaths/mutations/HGT, GA fitness/diversity).
   - These runs and summaries are generated into the validation report by: `backend/generate_validation_report.py`

3. **Comparison with real-world experimental/surveillance results (proof references)**
   - The project compares simulation behavior against **published real-world surveillance/experimental findings** (cited sources), not against newly performed wet-lab experiments.
   - The comparison demonstrates qualitatively consistent phenomena (selection pressure, resistance emergence/increase, scenario-dependent dynamics) and includes cited references (e.g. WHO GLASS, CDC antimicrobial resistance/MRSA threats, and uropathogen resistance guidance such as EAU context) in the report.

> **Jury note:** "Correct" in this context means the model behaves consistently with expected biological/evolutionary principles and shows qualitative agreement with cited real-world evidence for the mapped scenarios; it does not claim clinical-grade quantitative prediction without further calibration/validation.

## 4) Where is the comparison report?
- **Saved PDF (Desktop):** `C:\Users\kavan\OneDrive\Desktop\Microbial_GA_Validation_Report.pdf`
  - Includes: objectives verification, GA-enabled system test results for `hospital_surface_mrsa` and `uti_ecoli`, and comparison with real-world surveillance/experimental findings with cited proof references/sources and conclusions.
- **Generator script:** `backend/generate_validation_report.py`
  - Regenerate (from `backend`):
    - `python generate_validation_report.py`
  - Output path logic: saves to `~/OneDrive/Desktop` if present, otherwise `~/Desktop` as `Microbial_GA_Validation_Report.pdf`.

## 5) Where are the test case reports / test artifacts?
- **Automated test cases:** `backend/tests/test_ga_objectives.py`
  - Checks: GA metrics present in snapshots; scenario presets mapped (`hospital_surface_mrsa`, `uti_ecoli`).
- **Validation/system test results:** embedded in `C:\Users\kavan\OneDrive\Desktop\Microbial_GA_Validation_Report.pdf` (tables, metrics, trends for both scenarios).
- **Related implementation files (for traceability):**
  - `backend/simulation/genetic_algorithm.py` (GA operators)
  - `backend/simulation/engine.py` (GA integration, scenarios, metrics)
  - `backend/app.py` (scenario API)
  - `backend/ml/predictor.py` (ML hotspot/resistance risk prediction)

## 6) Quick demo checklist (for presentation)
1. Start backend/frontend and open dashboard.
2. Select a mapped scenario (MRSA hospital surface or E. coli UTI) and run simulation.
3. Show GA metrics (fitness/diversity/selection/crossover) and resistance/hotspot charts/heatmap.
4. Show ML risk/prediction panel.
5. Present `Microbial_GA_Validation_Report.pdf` and explain: internal tests + comparison against cited published real-world evidence.