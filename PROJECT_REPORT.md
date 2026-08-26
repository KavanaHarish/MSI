# Project Report — Microbial Evolution Simulator under Antibiotic Stress

**Generated:** 14 August 2026
**Repository:** `SIMU_NEW_VER` (git, branch `main`)
**Nature:** Final Year Engineering Major Project — biomedical research-style web platform.

---

## 1. Executive Summary

The **Microbial Evolution Simulator under Antibiotic Stress** is a full-stack
web platform that simulates bacterial reproduction, mutation, and natural
selection on a spatial grid under antibiotic pressure, then layers a
machine-learning model on top to forecast resistance trends. The project
implements every page and API route end-to-end with working (non-mocked)
simulation logic and ML predictions.

The system is organised as a three-stage pipeline matching the project spec:

```
Landing Page  →  How To Use  →  Simulation Dashboard
simulation generates data → ML analyzes it → ML predicts
```

### Key figures

| Dimension | Value |
|---|---|
| Frontend | React 18 + Vite 8 + Tailwind 3 + Three.js + Framer Motion + Recharts |
| Backend | Python 3.11 + Flask 3 |
| Science | NumPy, Pandas, scikit-learn (Random Forest) |
| Database | MongoDB Atlas (optional, in-memory fallback) |
| Source files (backend) | 6 Python modules |
| Source files (frontend) | 21 `.jsx`/`.js` files under `src/` |
| Largest source file | `PetriDish3D.jsx` (~1,200 active lines) |
| Git history | 19 commits on `main` |

---

## 2. Technology Stack

### Frontend (`frontend/`)
- **React 18.3** + **React Router 6.26** (4 routes)
- **Vite 8.2** build tooling with a `/api` proxy to Flask (port 5173 → 5000)
- **Tailwind CSS 3.4** design system (see §10)
- **Three.js 0.165** + postprocessing (bloom) for the 3D petri-dish renderer
- **Framer Motion 11** for page/UI transitions
- **Recharts 2.12** for live charts
- **jsPDF 4 + html2canvas** for client-side PDF laboratory reports
- **Axios** HTTP client for the Flask API
- **qrcode** dependency declared in `package.json`

### Backend (`backend/`)
- **Flask 3.0.3** with **Flask-Cors** (CORS restricted to `http://localhost:5173` by default)
- **NumPy 1.26 / Pandas 2.2** — grid math, diffusion kernels, analysis
- **scikit-learn 1.5** — RandomForestRegressor forecasting
- **pymongo 4.8** — MongoDB Atlas connector
- **reportlab 4.2** — declared for future server-side PDF generation
- **python-dotenv** — environment configuration

---

## 3. System Architecture

```
┌────────────────────────────  FRONTEND (React/Vite :5173)  ────────────────────────────┐
│                                                                                        │
│  pages: Landing · HowToUse · About · Dashboard                                         │
│  components: Navbar · Footer · ControlPanel · PetriDish3D · StatPanel · ChartsPanel ·  │
│              MLPanel · Timeline · GlassCard                                            │
│  context: SimulationContext  ── polling loop + shared state                             │
│  api/client.js: Axios wrapper for /api/*                                               │
│  utils/reportGenerator.js: client-side 8-page PDF builder                              │
└───────────────────────────────┬────────────────────────────────────────────────────────┘
                                │  HTTP (Vite proxy, no CORS friction in dev)
┌───────────────────────────────▼────────────────────────────────────────────────────────┐
│                            BACKEND (Flask :5000)                                       │
│  app.py            → REST routes, experiment registry (in-memory)                      │
│  config.py         → env-based configuration (secret key, CORS, Mongo)                 │
│  simulation/engine.py → SimulationEngine: grid, cells, antibiotic diffusion, mutation, │
│                         HGT/conjugation, per-generation snapshots                       │
│  ml/predictor.py   → analyze(history): RandomForest forecast, risk & recommendation     │
│  db/mongo.py       → MongoStore: experiment-level persistence + in-memory fallback      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

Key design decision (per spec): **the simulation engine never touches ML**.
`engine.py` only produces per-generation snapshots; `predictor.py` reads that
history *after the fact*. The engine is never steered by the model.

---

## 4. Backend Detail

### 4.1 `app.py` — API routes (189 lines)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Status + Mongo connectivity flag |
| POST | `/api/start` | Create experiment from config payload |
| POST | `/api/step` | Advance 1+ generations; persists snapshot per step |
| GET | `/api/state` | Live cells, antibiotic field (downsampled ×2), stats |
| GET | `/api/prediction` | ML forecast for the experiment |
| GET | `/api/history` | Full generation history (fallback to Mongo if engine cleared) |
| POST | `/api/reset` | Drop experiment from in-memory registry |
| POST | `/api/treat` | Apply targeted antibiotic treatment disk (lab feature) |
| GET | `/api/report` | JSON or CSV report download (attachment) |

Active simulations live in the module-level `ACTIVE_SIMULATIONS` dict keyed by
UUID experiment id. Per-bacterium data intentionally stays in server memory
and is **never** written to MongoDB.

### 4.2 `config.py` (26 lines)
Central env-driven config:
- `SECRET_KEY`, `DEBUG` (from `FLASK_DEBUG`)
- `CORS_ORIGINS` (comma-separated, default localhost:5173)
- `MONGO_URI`, `MONGO_DB_NAME` (`microbial_evolution_sim`)
- `MONGO_OPTIONAL` — when `1` (default), app runs without a live Mongo connection

### 4.3 `simulation/engine.py` (362 lines) — Core biology model

**Species profiles** — 11 clinically relevant ESKAPE-pathogen bacteria
(`SPECIES_PROFILES`): E. coli, MRSA, Pseudomonas, K. pneumoniae, Acinetobacter,
E. faecium, S. pneumoniae, Salmonella, N. gonorrhoeae, E. cloacae,
H. influenzae — each with its own base growth and mutation rate.

**Cell model** (`Cell`, `__slots__`-optimised):
- Grid position `(x, y)`, scalar `resistance` ∈ [0,1], mutation counter.
- Resistance classified into 4 phenotypes via `classify()`:
  - `< 0.25` Susceptible · `< 0.50` Intermediate · `< 0.75` Resistant · `≥ 0.75` Highly Resistant.

**Simulation loop (`step()`), one generation:**
1. `_diffuse_antibiotic()` — 2D diffusion kernel (neighbour average) + decay clamp.
2. **Selection** — survival chance = `1 − max(0, local_ab − resistance)`; cells
   under a high local concentration with low resistance die.
3. **Spatial occupancy** — one cell per grid cell (competition for space).
4. **Reproduction** — binary fission to a random free neighbour at `growth_rate`;
   capped by `max_population` (= initial × 12, min 800).
5. **Mutation** — with `mutation_rate × 3`, child resistance jumps by a random
   delta scaled by `mutation_strength`.
6. `_horizontal_gene_transfer()` — **conjugation**: a cell with resistance ≥ 0.5
   donates plasmids to an adjacent cell, pulling the recipient 50% toward its
   own resistance. Donors are snapshotted so no one-pass cascade occurs. This
   models the lateral "explosive" resistance sweeps seen in microbiology.

**Lab intervention** — `apply_treatment(intensity, x, y, drug)` superimposes a
localized diffusion gradient (Kirby–Bauer style disk), capped at 2.0 for
supra-MIC shock doses, and appends to `interventions_log`.

**Snapshot metrics** (one per generation): population, avg resistance,
resistant fraction, deaths, mutations, HGT events, cumulative counters,
survival rate, hotspot count, dominant colony class.

### 4.4 `ml/predictor.py` (179 lines) — Forecasting layer

Requires ≥ 6 history points (`MIN_POINTS_FOR_PREDICTION`), else returns a
"collecting data" message.

- **Model**: `RandomForestRegressor` (60 trees, depth 6) trained on 7-feature
  state vectors → next-generation average resistance.
- **Forecast**: recursive 20-generation (`FORECAST_HORIZON`) forward pass.
- **Confidence**: R² penalised by residual scatter (erratic histories score lower).
- **Dominance**: first generation where projected resistance ≥ 0.70.
- **Risk zone** (score 0–100): hotspots, resistance slope, population density,
  mutation velocity, death rate — high risk when score ≥ 50.
- **Antibiotic effectiveness** from resistance slope; plain-language
  **recommendation** assembled from detected signals.

### 4.5 `db/mongo.py` (90 lines)
`MongoStore` connects to Atlas with a 3 s selection timeout. On failure it
prints a warning and falls back to an **in-memory dict store** (still
functional for the current process). Stores only **experiment-level** data:
experiments, snapshots, reports — never per-bacterium records.

---

## 5. Frontend Detail

### 5.1 Routing (`App.jsx`, `main.jsx`)
BrowserRouter + SimulationProvider wraps 4 routes:
`/` (Landing), `/how-to-use` (HowToUse), `/about` (About), `/dashboard` (Dashboard).
Page transitions via `AnimatePresence`; footer hidden on the dashboard.

### 5.2 `context/SimulationContext.jsx` (136 lines) — global state
Owns config, experiment id, latest state, history, prediction, running flag,
and start error. Central to the app is the **polling loop**:
- `start()` → POST `/api/start`, then `setInterval` ticks at
  `max(120, 700 / speed)` ms.
- `tick()` → POST `/api/step` (1 gen), appends stats to history (capped 200),
  re-fetches `/api/prediction` every 3 generations.
- `pause()` / `resume()` / `reset()` / `refreshHistory()` / `applyTreatment()`.

### 5.3 `components/`
- **ControlPanel.jsx** (424 lines) — species + antibiotic selection, 8 parameter
  sliders, start/pause/resume/reset, lab-intervention treatment disk (x/y +
  concentration in ×MIC), JSON/CSV export links. Species→antibiotic mapping is
  curated per organism.
- **PetriDish3D.jsx** (~1,200 active lines) — Three.js instanced-mesh renderer
  (max 3,500 cells): glass petri rim, agar plate, additive-blended antibiotic
  heatmap texture, bloom postprocessing, orbit controls, per-class colors
  (green→yellow→orange→red→gray), hover telemetry card, and a 7-stage
  timeline overlay. *(Note: ~460 lines of earlier drafts remain as comments at
  the top of the file.)*
- **StatPanel.jsx** — live statistics rows (generation, population, avg
  resistance, mutations, HGT, deaths, survival, dominant colony, hotspots).
- **ChartsPanel.jsx** — 4 Recharts line charts (population, resistance, deaths,
  mutations) over generation history.
- **MLPanel.jsx** — forecast cards (dominant generation, effectiveness,
  confidence, risk zone) + recommendation text.
- **Timeline.jsx** — derived research-log of notable events (mutations, HGT,
  dominance transitions, hotspots), newest first.
- **Navbar.jsx** — fixed capsule nav (Home / Explore / About Us).
- **Footer.jsx**, **GlassCard.jsx** — shared layout primitives.

### 5.4 `pages/`
- **Landing.jsx** (377 lines) — marketing/hero landing.
- **HowToUse.jsx** (395 lines) — guided walkthrough of the lab workflow.
- **About.jsx** (76 lines) — project description + institution; uses a distinct
  light-on-dark "earth/emerald" theme (note: styled differently from the
  navy/gold dashboard theme).
- **Dashboard.jsx** (121 lines) — 3-column lab console (controls | 3D dish |
  stats) plus report download, charts, ML panel, and timeline.

### 5.5 `utils/reportGenerator.js` (697 lines) — client-side PDF
Builds an **8-page A4 PDF** entirely in the browser (jsPDF + html2canvas):

1. **Cover** — branded header, SVG biology illustration, metadata block.
2. **Experiment Configuration** — organism, antibiotic, 10 parameters.
3. **Live Results** — 6 metric cards.
4. **Scientific Charts** — 5 SVG trend charts (population, resistance,
   mutations, survival, death rate).
5. **Final Colony Snapshot** — WebGL canvas capture (with html2canvas fallback)
   + phenotype/field color legend.
6. **Biological Analysis** — 5 narrative sections.
7. **Experimental Observations** — checklist-style observations.
8. **Interpretation & Recommendations** — circular gauges, diagnostic bars,
   drug recommendation.

Filename is sanitised and timestamped (`Microbial_Report_<species>_<drug>_<date>.pdf`).

---

## 6. API Reference (summary)

See §4.1. All endpoints are JSON except `/api/report?format=csv|json` which
returns attachments. `/api/state` down-samples the antibiotic field 2× for
payload size. History is capped client-side to the last 200 snapshots.

---

## 7. File Inventory (source, exluding vendored dirs)

```
backend/
├── app.py                        152  REST API + experiment registry
├── config.py                      19  env config
├── requirements.txt                9  dependencies
├── .env.example                   11  env template
├── simulation/engine.py          315  core evolution engine
├── ml/predictor.py               158  ML forecasting
├── db/mongo.py                    77  Mongo store + fallback
└── (db/, ml/, simulation/ __init__.py)

frontend/src/
├── main.jsx                       15  entry point
├── App.jsx                        28  routing shell
├── index.css                      93  Tailwind + component classes
├── api/client.js                  21  Axios API wrapper
├── context/SimulationContext.jsx 120  global state + polling
├── utils/reportGenerator.js      697  PDF report builder
├── pages/
│   ├── Dashboard.jsx             111  lab console
│   ├── Landing.jsx               377  landing page
│   ├── HowToUse.jsx              395  walkthrough
│   └── About.jsx                  76  about page
└── components/
    ├── PetriDish3D.jsx          1203  Three.js renderer (active)
    ├── ControlPanel.jsx          401  controls + treatments
    ├── Footer.jsx                127
    ├── Navbar.jsx                 76
    ├── ChartsPanel.jsx            87
    ├── MLPanel.jsx                73
    ├── StatPanel.jsx              62
    ├── Timeline.jsx               62
    └── GlassCard.jsx              21

frontend/
├── package.json                   30  scripts + dependencies
├── vite.config.js                 15  dev server + /api proxy
├── tailwind.config.js             65  design tokens
├── index.html                    (entry HTML)
```

---

## 8. Design System

Defined in `tailwind.config.js` + `index.css`:

| Token | Value | Use |
|---|---|---|
| Deep Navy | `#0B1220` | primary background |
| Dark Charcoal | `#171B21` | panels/surfaces |
| Medical White | `#F4F6F9` | body text |
| Royal Gold | `#D4AF37`/`#C89B3C`/`#B8860B` | primary accent, buttons |
| Soft Cyan | `#6FD8E8` | secondary accent, eyebrows |
| Emerald | `#2ECC91` | positive/success states |
| Display font | Cinzel | headings |
| Body font | Inter | body |
| Data/UI font | Manrope | labels/data |

Reusable component classes: `glass-panel`, `glass-pill`, `btn-gold`,
`btn-outline`, `btn-report`, `section-eyebrow`, `title-serif`, `lab-select`.
Custom animations: `pulseGlow`, `driftSlow`. Reduced-motion support included.

---

## 9. Running the Project

**Backend**
```bash
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # optional: real MongoDB URI
python app.py          # http://localhost:5000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxies /api → :5000)
```

**Production**
```bash
cd frontend && npm run build   # static files → dist/
# serve dist + Flask under gunicorn/uwsgi with FLASK_DEBUG=0
```

MongoDB Atlas is optional locally — the backend falls back to in-memory
storage when `MONGO_URI` is a placeholder or unreachable.

---

## 10. Git History

```
13bcb01 added colors to the simulation cells based on their evolution
7023223 edited landing page
a6e1137 pdf updates and Simulation
a89eb61 changed footer
cac9e36 Merge branch 'main' (remote)
901ab2c Grid
17db346 restore: re-add Footer.jsx with fixed content
074078f fix: restore Footer.jsx
d28da46 Merge remote main and resolve footer conflict
a34e180 changed footer
fed1b6f Edited the simulation part
b333208 changes in landing page
590e67b added a lot of stuff
c76cd0c initial setup
```

Working tree currently has uncommitted edits across ~30 files and one
untracked file (`frontend/src/pages/About.jsx`); branch is 2 commits behind
`origin/main`.

---

## 11. Current State & Observations

**Working:** Full end-to-end pipeline — experiment start → live stepping →
ML predictions → charting → JSON/CSV export → 8-page PDF report → targeted
lab treatments (antibiotic disks) with HGT conjugation.

**Code-health notes:**
1. `PetriDish3D.jsx` contains ~460 lines of commented-out legacy drafts above
   the active implementation — candidates for cleanup.
2. `About.jsx` uses a different visual theme (earth/emerald, Pally font) from
   the rest of the app (navy/gold).
3. `predictor.py` has one subtlety: the per-feature `_feature_vector` reads
   `h["survival_rate"]` etc.; future snapshot schema changes must stay in sync.
4. `package-lock copy.json` sits in the repo root of `frontend` (a stray copy).
5. Backend `venv/` and `__pycache__` are present locally but ignored by git.
6. No automated tests or CI configured yet.
7. API client, context, and engine all assume a single experiment at a time
   (no multi-user isolation).

---

## 12. Suggested Next Steps

1. Strip commented legacy drafts from `PetriDish3D.jsx`.
2. Unify `About.jsx` styling with the dashboard theme (or intentionally keep).
3. Add PDF report generation server-side (reportlab already declared) as an
   alternative to the client-side HTML snapshot pipeline.
4. Add authentication + per-user experiment isolation if multi-user is needed.
5. Upgrade the ML layer to a time-series model (e.g., ARIMA/LSTM) if the
   academic report requires more than RandomForest.
6. Add tests (pytest for engine/predictor; Vitest for context/API) and a CI
   pipeline.
7. Deploy: frontend → Vercel/Netlify, backend → Render/Railway,
   MongoDB → Atlas free tier (fill in real `MONGO_URI`).
8. Resolve the 2-commit drift with `origin/main` and commit the current work.
