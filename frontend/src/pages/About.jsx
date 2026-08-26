import { motion } from "framer-motion";
import { Link } from "react-router-dom";

const TEAM = [
  {
    role: "Department of Information Science & Engineering",
    name: "Team BRAINROT",
    desc: "Biotechnology experimental report pipeline and microbial cellular-automaton simulation platform built as a capstone research project.",
  },
];

const VALUES = [
  { title: "Spatial Realism", desc: "Agent-based cells evolve on a diffusion grid with antibiotic concentration gradients and treatment hotspots." },
  { title: "Forecasting", desc: "A lightweight ML model estimates dominant-generation and drug effectiveness trajectories from live history." },
  { title: "Reproducibility", desc: "Full experiment history exports as JSON / CSV and a generated PDF laboratory report." },
];

export default function About() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
      style={{ fontFamily: "'Pally', sans-serif" }}
      className="bg-[#0c0d0c] min-h-screen text-white pt-36"
    >
      <section className="max-w-6xl mx-auto px-6 py-16">
        <p className="text-earth-300 font-bold tracking-widest uppercase text-sm mb-4">About Us</p>
        <h1 className="font-bold text-4xl md:text-5xl text-white mb-8 leading-tight">
          Decoding Resistance. One Generation at a Time.
        </h1>
        <p className="text-white/75 leading-relaxed font-medium text-lg text-justify max-w-3xl mb-12">
          The Microbial Evolution Simulator is a computational platform for simulating bacterial
          reproduction, mutation, and selection under antibiotic stress. It models how resistance
          emerges and spreads across a living colony on a spatial grid, and layers a machine-learning
          model on top to forecast where resistance is heading.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {VALUES.map((v, i) => (
            <motion.div
              key={v.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.5, delay: (i % 4) * 0.08 }}
              className="bg-white/5 border border-white/5 rounded-[2rem] p-7 hover:border-emerald-300/40 transition-all duration-300 backdrop-blur-sm"
            >
              <h3 className="font-bold text-emerald-300 text-base tracking-wide mb-3">{v.title}</h3>
              <p className="font-medium text-white/70 leading-relaxed text-sm">{v.desc}</p>
            </motion.div>
          ))}
        </div>

        {TEAM.map((t) => (
          <motion.div
            key={t.name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5 }}
            className="bg-white/5 border border-white/5 rounded-[2rem] p-8 hover:border-emerald-300/40 transition-all duration-300 backdrop-blur-sm"
          >
            <p className="text-xs font-bold tracking-widest text-earth-300 uppercase mb-2">{t.role}</p>
            <h3 className="font-bold text-2xl text-white mb-3">{t.name}</h3>
            <p className="font-medium text-white/70 leading-relaxed text-sm max-w-3xl">{t.desc}</p>
          </motion.div>
        ))}

        <div className="mt-12">
          <Link
            to="/dashboard"
            className="inline-block px-8 py-3.5 rounded-full bg-[#fecf33] text-[#0c0d0c] font-bold uppercase tracking-widest hover:bg-emerald-400 hover:-translate-y-0.5 transition-all duration-300 shadow-lg shadow-emerald-300/20"
          >
            Launch Laboratory
          </Link>
        </div>
      </section>
    </motion.div>
  );
}
