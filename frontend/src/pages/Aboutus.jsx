import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

export default function AboutUs() {
  const navigate = useNavigate();

  const teamMembers = [
    { 
      name: 'Adarsh M', 
      id: '1VA23IS002', 
      email: 'adarshm.reach@gmail.com',
      role: 'Project Innovator'
    },
    { 
      name: 'Janani V', 
      id: '1VA23IS038', 
      email: 'jananiv.23is@saividya.ac.in',
      role: 'Creative Developer'
    },
    { 
      name: 'Kavana H', 
      id: '1VA23IS045', 
      email: 'kavanahpoojary@gmail.com',
      role: 'Creative Developer'
    },
    { 
      name: 'Shreya P Shetty', 
      id: '1VA23IS099', 
      email: 'shreyapshetty@gmail.com',
      role: 'Research & Design'
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.15 }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 30 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } }
  };

  return (
    // Locked to exactly 1 screen height, no scrolling allowed
    <div className="h-screen bg-[#080f08] text-white selection:bg-[#e4c590] selection:text-black overflow-hidden font-body relative flex flex-col">
      
      {/* ── HIGH-RES BACKGROUND ── */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <img 
          src="https://images.pexels.com/photos/28710291/pexels-photo-28710291.jpeg" 
          alt="Background" 
          className="w-full h-full object-cover opacity-60"
        />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(8,15,8,0.4)_0%,rgba(8,15,8,0.95)_100%)] z-10" />
      </div>

      
        

      {/* ── MAIN CONTENT ── */}
      <div className="relative z-30 flex-1 flex flex-col justify-center items-center px-4 md:px-6 pt-20 pb-8">
        
        {/* Hero Headers - Scaled down and margins reduced */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}
          className="text-center mb-8 md:mb-12"
        >
          <p className="font-kannada text-[#e4c590] text-xl md:text-2xl mb-2 drop-shadow-md"></p>
          <h1 className="text-5xl md:text-7xl font-display font-bold uppercase tracking-tighter drop-shadow-2xl">
            The <span className="text-[#e4c590] italic">Creators</span>
          </h1>
          <p className="text-white/70 tracking-[0.3em] uppercase text-[10px] md:text-xs mt-4 font-medium bg-black/30 px-4 py-1.5 rounded-full backdrop-blur-sm inline-block">
           • Team BrainRot •
          </p>
        </motion.div>

        {/* ── GLASSMORPHISM CARDS GRID ── */}
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="show"
          // Reduced gap to fit nicely on one screen
          className="grid grid-cols-1 md:grid-cols-4 gap-10 w-full max-w-6xl"
        >
          {teamMembers.map((member, index) => (
            <motion.div 
              key={index}
              variants={cardVariants}
              whileHover={{ y: -10 }}
              // Reduced padding (p-6) and border radius slightly
              className="group relative bg-black/40 backdrop-blur-xl border border-white/10 rounded-[2rem] p-2 md:p-2 flex flex-col items-center text-center shadow-[0_20px_50px_rgba(0,0,0,0.5)] transition-colors duration-500 "
            >
              <div className="absolute inset-0 bg-[#10b981]/0 group-hover:bg-[#10b981]/5 rounded-[2rem] transition-colors duration-500 pointer-events-none" />

              {/* Avatar Circle - Scaled down slightly */}
              <div className="relative w-20 h-20 mb-5 flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-2 border-dashed border-[#e4c590]/30 group-hover:border-[#e4c590] group-hover:animate-[spin_10s_linear_infinite] transition-colors duration-500" />
                <div className="w-16 h-16 rounded-full bg-[#080f08] border border-white/10 flex items-center justify-center shadow-inner z-10 group-hover:shadow-[0_0_20px_rgba(228,197,144,0.4)] transition-shadow duration-500">
                  <span className="text-2xl font-display font-bold text-[#e4c590]">
                    {member.name.charAt(0)}
                  </span>
                </div>
              </div>

              {/* Text Details - Tighter spacing */}
              <h3 className="text-2xl font-display font-bold text-white mb-1 group-hover:text-[#10b981] transition-colors duration-300">
                {member.name}
              </h3>
              
              <p className="text-xs font-body text-white/60 italic mb-3">
                {member.role}
              </p>
              
              <div className="w-8 h-[1px] bg-white/20 mb-4 group-hover:bg-[#10b981]/50 transition-colors" />
              
              <div className="mb-6">
                <p className="text-[10px] uppercase tracking-[0.4em] text-white/50 mb-1.5 font-bold">
                  {member.id}
                </p>
                <p className="text-[10px] tracking-widest text-[#e4c590]/80 font-body">
                  {member.email}
                </p>
              </div>

              {/* Action Button - Scaled down for compactness */}
              <a 
                href={`mailto:${member.email}`}
                className="mt-auto px-6 py-2.5 border border-white/20 rounded-full text-xs font-body text-white/70 tracking-widest hover:bg-[#10b981] hover:text-black hover:border-[#10b981] transition-all duration-300 z-10 shadow-lg"
              >
                Say Hello
              </a>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}