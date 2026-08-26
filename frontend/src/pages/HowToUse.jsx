import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import GlassCard from "../components/GlassCard.jsx";

const CONTROLS = [
  {
    name: "Species & Antibiotic",
    desc: "Pick one of eleven clinically relevant bacteria (E. coli, K. pneumoniae, P. aeruginosa, A. baumannii, E. faecium, S. pneumoniae, MRSA, S. enterica, N. gonorrhoeae, E. cloacae, H. influenzae) and a matching antimicrobial agent.",
  },
  {
    name: "Treatment Concentration",
    desc: "Mid-simulation, apply a custom antibiotic dose from 0–2× MIC. Concentrations above 1.0 (supra-MIC shock dose) kill even resistant cells — watch the population drop next generation.",
  },
  {
    name: "Initial Population",
    desc: "The number of cells seeded onto the dish at generation 0. Larger populations create denser colonies and stronger competition for space.",
  },
  {
    name: "Mutation Rate",
    desc: "The probability that a reproducing cell's offspring acquires a random change in resistance. Higher values accelerate the emergence of new resistant variants.",
  },
  {
    name: "Mutation Strength",
    desc: "How far a mutation can shift an offspring's resistance away from its parent. Higher values produce more dramatic jumps in resistance per event.",
  },
  {
    name: "HGT Rate (Conjugation)",
    desc: "The probability per generation that a resistant cell shares resistance genes (plasmids) with an adjacent neighbor. Horizontal transfer bypasses reproduction entirely — even a few resistant donors can pull whole colonies up to high resistance within a handful of generations.",
  },
  {
    name: "Antibiotic Level",
    desc: "The baseline concentration of antibiotic across the dish. Cells whose resistance falls below the local concentration are more likely to die each generation.",
  },
  {
    name: "Growth Rate",
    desc: "The probability that a surviving cell reproduces in a given generation. Higher growth rates increase population pressure on available space.",
  },
  {
    name: "Grid Size",
    desc: "The resolution of the simulated petri dish. Larger grids allow more spatial detail but take marginally longer to compute per generation.",
  },
  {
    name: "Simulation Speed",
    desc: "How quickly generations advance once the experiment is running. This only affects playback pace, not the underlying biology.",
  },
];

const GRID_LEGEND = [
  { label: "Susceptible (viable)", color: "#34D399" },
  { label: "Intermediate resistance", color: "#FFD54A" },
  { label: "Resistant variant", color: "#FF8C32" },
  { label: "Highly resistant (superbug)", color: "#FF3B3B" },
  { label: "Dead (lysis)", color: "#334155" },
  { label: "Antibiotic concentration heatmap", color: "linear-gradient(135deg, #32E6FF, #7B2CFF)" },
];

const OUTPUTS = [
  { name: "Live Statistics", desc: "A live panel tracking generation, population, average resistance, mutation count, HGT (plasmid) transfer count, death/survival rates, dominant colony class, and hotspot count." },
  { name: "Charts", desc: "Four real-time charts — population, average resistance, deaths per generation, and cumulative mutations — plotted against generation." },
  { name: "ML Prediction", desc: "A scikit-learn random forest trained on the live simulation log models resistance dynamics and projects the next 20 generations, estimating dominant-generation, antibiotic effectiveness, dynamic confidence, and an actionable risk zone." },
  { name: "Timeline", desc: "A chronological research log recording mutations, resistance increases, and hotspot detections." },
  { name: "Heatmap", desc: "The antibiotic concentration field rendered directly onto the 3D petri dish surface — high concentration zones glow electric blue/purple." },
  { name: "Reports", desc: "Export the full experiment history as JSON or CSV, or download a generated PDF laboratory report." },
];

const WORKFLOW_STEPS = [
  {
    title: "Select Organism & Antibiotic",
    desc: "Pick one of eleven bacteria and a matching antimicrobial agent from 72 species–antibiotic combinations.",
  },
  {
    title: "Tune Parameters",
    desc: "Adjust initial population, mutation rate and strength, HGT rate, antibiotic level, growth rate, grid size, and simulation speed to shape the experiment.",
  },
  {
    title: "Start Simulation",
    desc: "Cells reproduce, mutate, and die under the antibiotic gradient, generation by generation, rendered live on the 3D petri dish.",
  },
  {
    title: "Intervene",
    desc: "Pause the run, or apply targeted treatment doses up to 2× MIC to test dosing strategies mid-experiment.",
  },
  {
    title: "Export Results",
    desc: "Download the full generation history as JSON or CSV, or generate an 8-page PDF laboratory report.",
  },
];

const MODEL_RULES = [
  {
    title: "Reproduction & Mutation",
    desc: "Each surviving cell may reproduce into an adjacent empty cell. Offspring inherit parental resistance; a mutation shifts it by a random amount up to the configured mutation strength.",
  },
  {
    title: "Horizontal Gene Transfer",
    desc: "Independently of reproduction, a cell with resistance ≥ 0.5 can conjugate with a random adjacent cell each generation, transferring a fraction of the gap in resistance. This lateral sharing produces explosive, non-linear resistance sweeps that vertical mutation alone cannot match.",
  },
  {
    title: "Survival Rule",
    desc: "Every generation, a cell survives with chance 1 − max(0, local antibiotic concentration − cell resistance). Cells whose resistance falls below the local concentration are increasingly likely to die.",
  },
  {
    title: "Antibiotic Diffusion",
    desc: "Concentration spreads across the grid each generation (four-direction diffusion) and slowly decays, staying within 0.1–2.0.",
  },
  {
    title: "Treatment Concentration",
    desc: "Mid-run doses range from 0 to 2× MIC. Values above 1.0 act as a supra-MIC shock dose that can kill even resistant cells. Deaths from a dose resolve on the next generation.",
  },
  {
    title: "Hotspots",
    desc: "Cells with resistance ≥ 0.75 inside a high-pressure zone (concentration > 0.6) are flagged as hotspots — an early warning of selection pressure concentrating.",
  },
];

const LAB_CONTROLS = [
  { name: "Pause / Resume / Reset", desc: "Freeze the run at the current generation, continue it, or wipe the dish and return to the configuration screen." },
  { name: "Apply Treatment", desc: "Drop a targeted antibiotic dose anywhere on the grid with a chosen concentration (0–2× MIC) and optional x/y coordinates for the center of the zone." },
];

const ML_METRICS = [
  { name: "Estimated Dominant Generation", desc: "The generation where a random-forest forecast projects average resistance crossing the 0.7 dominance threshold." },
  { name: "Antibiotic Effectiveness", desc: "A 0–100 score that falls as resistance accelerates, signalling the current dose is losing efficacy." },
  { name: "Confidence Score", desc: "Calculated dynamically from the model fit (R²) minus residual scatter. Chaotic, erratic histories score low; smooth trends score high." },
  { name: "Risk Zone", desc: "A weighted score from live hotspot count, resistance slope, population density, mutation velocity, and death rate. Crosses into High at 50/100." },
];

const EXPORT_OPTIONS = [
  { name: "JSON", desc: "The complete experiment history and metadata as machine-readable JSON." },
  { name: "CSV", desc: "A flat per-generation table (population, resistance, deaths, mutations, survival, hotspots) for spreadsheets." },
  { name: "PDF Report", desc: "An 8-page laboratory report: cover, configuration, live metrics, charts, colony snapshot, biological analysis, observations, and  interpretation." },
];

export default function HowToUse() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      className="pt-32"
    >
      <section className="max-w-4xl mx-auto px-6 text-center mb-20">
        <p className="section-eyebrow mb-4">Documentation</p>
        <h1 className="title-serif text-4xl md:text-5xl text-medical-white mb-6">
          Laboratory Guide
        </h1>
        <p className="font-body text-medical-white/65 text-lg">
          Learn how to configure and understand your experiment before
          entering the simulation dashboard.
        </p>
      </section>

      {/* Section 1: control specifications */}
      <section className="max-w-6xl mx-auto px-6 py-16 grid grid-cols-1 lg:grid-cols-2 gap-14 items-start">
        <GlassCard hover={false} className="!p-4">
          <div className="rounded-xl overflow-hidden bg-navy-deep/90 p-5 border border-cyan-400/20 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <span className="text-xs font-data text-cyan-soft uppercase tracking-wider">🔬 Experiment Config</span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30">Ready</span>
            </div>
            <div className="space-y-3 font-data text-xs">
              <div>
                <label className="text-medical-white/60 block mb-1">Target Organism</label>
                <div className="bg-charcoal p-2 rounded border border-white/10 text-gold-400">Escherichia coli (E. coli)</div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-medical-white/60 block mb-1">Mutation Rate</label>
                  <div className="bg-charcoal p-2 rounded border border-white/10 text-cyan-soft">5.0%</div>
                </div>
                <div>
                  <label className="text-medical-white/60 block mb-1">Antibiotic Conc.</label>
                  <div className="bg-charcoal p-2 rounded border border-white/10 text-cyan-soft">50.0%</div>
                </div>
              </div>
              <div className="pt-2">
                <div className="w-full py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold text-center text-xs shadow-lg">
                  ▶ Start Simulation Experiment
                </div>
              </div>
            </div>
          </div>
        </GlassCard>

        <div>
          <p className="section-eyebrow mb-4">Configuration</p>
          <h2 className="title-serif text-3xl text-medical-white mb-8">
            Understanding the Controls
          </h2>
          <div className="flex flex-col gap-4">
            {CONTROLS.map((c, i) => (
              <GlassCard key={c.name} delay={i * 0.05} className="!p-4">
                <p className="font-body font-semibold text-gold-400 mb-1">
                  {c.name}
                </p>
                <p className="text-sm font-body text-medical-white/65 leading-relaxed">
                  {c.desc}
                </p>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>

      {/* Workflow: end-to-end experiment */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-14">
          <p className="section-eyebrow mb-4">Workflow</p>
          <h2 className="title-serif text-3xl text-medical-white">
            Running an Experiment, Step by Step
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {WORKFLOW_STEPS.map((s, i) => (
            <GlassCard key={s.title} delay={(i % 3) * 0.08}>
              <div className="flex items-start gap-3 mb-2">
                <span className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500/30 to-purple-600/30 border border-cyan-400/40 flex items-center justify-center text-xs font-data text-cyan-300 font-bold">
                  {i + 1}
                </span>
                <p className="font-display text-gold-500 tracking-wide pt-1">
                  {s.title}
                </p>
              </div>
              <p className="text-sm font-body text-medical-white/65 leading-relaxed">
                {s.desc}
              </p>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* Section 2: grid environment */}
      <section className="max-w-6xl mx-auto px-6 py-16 grid grid-cols-1 lg:grid-cols-2 gap-14 items-start">
        <div className="order-2 lg:order-1">
          <p className="section-eyebrow mb-4">Visualization</p>
          <h2 className="title-serif text-3xl text-medical-white mb-6">
            Reading the Grid Environment
          </h2>
          <p className="font-body text-medical-white/65 leading-relaxed mb-6">
            The 3D petri dish renders every living cell as a glowing,
            color-coded bacterium layered above an antibiotic concentration
            heatmap. Together they show not just how many bacteria survive,
            but where and why.
          </p>
          <div className="flex flex-col gap-3">
            {GRID_LEGEND.map((l) => (
              <div key={l.label} className="flex items-center gap-3">
                <span
                  className="w-4 h-4 rounded-full shrink-0"
                  style={{ background: l.color }}
                />
                <span className="text-sm font-body text-medical-white/70">
                  {l.label}
                </span>
              </div>
            ))}
          </div>
          <p className="font-body text-medical-white/65 leading-relaxed mt-6">
            <span className="text-gold-400 font-semibold">Hotspots</span> are
            regions where resistant cells cluster under high antibiotic
            pressure an early warning sign of selection pressure
            concentrating in one area of the colony.
          </p>
        </div>
        <GlassCard hover={false} className="!p-4 order-1 lg:order-2">
          <div className="rounded-xl overflow-hidden bg-navy-deep/90 p-5 border border-purple-500/20 shadow-xl flex flex-col items-center justify-center min-h-[260px] relative">
            <div className="w-40 h-40 rounded-full border-2 border-cyan-400/40 bg-radial from-purple-900/40 via-navy to-charcoal flex items-center justify-center relative shadow-[0_0_30px_rgba(56,189,248,0.25)]">
              <div className="absolute w-3 h-3 rounded-full bg-cyan-400 top-8 left-10 animate-ping" />
              <div className="absolute w-2.5 h-2.5 rounded-full bg-gold-400 bottom-10 right-8" />
              <div className="absolute w-3 h-3 rounded-full bg-red-400 top-12 right-12" />
              <div className="absolute w-2 h-2 rounded-full bg-cyan-300 bottom-12 left-12" />
              <div className="text-[10px] font-data text-cyan-soft/80">3D Cellular Grid</div>
            </div>
            <div className="mt-4 text-xs font-data text-medical-white/60">Real-time Microbial Colony Surface</div>
          </div>
        </GlassCard>
      </section>

      {/* Model mechanics */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-14">
          <p className="section-eyebrow mb-4">Model Mechanics</p>
          <h2 className="title-serif text-3xl text-medical-white">
            How the Simulation Works
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {MODEL_RULES.map((r, i) => (
            <GlassCard key={r.title} delay={(i % 3) * 0.08}>
              <p className="font-display text-gold-500 tracking-wide mb-2">
                {r.title}
              </p>
              <p className="text-sm font-body text-medical-white/65 leading-relaxed">
                {r.desc}
              </p>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* Mid-experiment controls */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-14">
          <p className="section-eyebrow mb-4">Lab Interventions</p>
          <h2 className="title-serif text-3xl text-medical-white">
            Mid-Experiment Controls
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {LAB_CONTROLS.map((c, i) => (
            <GlassCard key={c.name} delay={(i % 3) * 0.08}>
              <p className="font-display text-gold-500 tracking-wide mb-2">
                {c.name}
              </p>
              <p className="text-sm font-body text-medical-white/65 leading-relaxed">
                {c.desc}
              </p>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* Section 3: output explanation */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-14">
          <p className="section-eyebrow mb-4">Interpretation</p>
          <h2 className="title-serif text-3xl text-medical-white">
            Understanding Your Results
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {OUTPUTS.map((o, i) => (
            <GlassCard key={o.name} delay={(i % 3) * 0.08}>
              <p className="font-display text-gold-500 tracking-wide mb-2">
                {o.name}
              </p>
              <p className="text-sm font-body text-medical-white/65 leading-relaxed">
                {o.desc}
              </p>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* ML prediction guide */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-14">
          <p className="section-eyebrow mb-4">Machine Learning</p>
          <h2 className="title-serif text-3xl text-medical-white">
            Reading the ML Prediction
          </h2>
          <p className="font-body text-medical-white/65 text-lg max-w-2xl mx-auto mt-4">
            Once at least six generations of history exist, a lightweight
            scikit-learn random forest trained on the live simulation log
            models the resistance dynamics and projects the next 20
            generations. The panel reports four metrics.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {ML_METRICS.map((m, i) => (
            <GlassCard key={m.name} delay={(i % 4) * 0.08}>
              <p className="font-display text-gold-500 tracking-wide mb-2">
                {m.name}
              </p>
              <p className="text-sm font-body text-medical-white/65 leading-relaxed">
                {m.desc}
              </p>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* Export guide */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-14">
          <p className="section-eyebrow mb-4">Data & Reports</p>
          <h2 className="title-serif text-3xl text-medical-white">
            Exporting Your Results
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {EXPORT_OPTIONS.map((e, i) => (
            <GlassCard key={e.name} delay={(i % 3) * 0.08}>
              <p className="font-display text-gold-500 tracking-wide mb-2">
                {e.name}
              </p>
              <p className="text-sm font-body text-medical-white/65 leading-relaxed">
                {e.desc}
              </p>
            </GlassCard>
          ))}
        </div>
      </section>

      {/* Section 4: proceed to laboratory */}
      <section className="max-w-4xl mx-auto px-6 py-16 text-center">
        <h2 className="title-serif text-3xl text-medical-white mb-4">
          Ready to Experiment?
        </h2>
        <p className="font-body text-medical-white/65 leading-relaxed mb-8">
          You're all set. Head into the laboratory to configure your species,
          antibiotic, and simulation parameters, then run your own experiment.
        </p>
        <Link
          to="/dashboard"
          className="inline-block px-10 py-4 rounded-full bg-[#fecf33] text-[#0c0d0c] font-bold uppercase tracking-widest hover:bg-emerald-400 hover:-translate-y-0.5 transition-all duration-300 shadow-lg shadow-emerald-300/20"
        >
          Enter Laboratory
        </Link>
      </section>
    </motion.div>
  );
}
