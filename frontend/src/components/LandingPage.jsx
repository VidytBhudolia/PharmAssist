import { motion } from "framer-motion";
import { TrendingUp, Globe, Shield, Activity, BookOpen, Zap, AlertCircle, Bot } from "lucide-react";

// Stagger animation for children
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 12,
    },
  },
};

const colorClasses = {
  blue: {
    gradient: "from-sky-500/8 via-transparent to-transparent",
    border: "border-border/70 hover:border-sky-400/60",
    icon: "bg-sky-500/15 border-sky-500/30",
    iconColor: "text-sky-400",
  },
  teal: {
    gradient: "from-teal-500/10 via-transparent to-transparent",
    border: "border-border/70 hover:border-teal-400/60",
    icon: "bg-teal-500/15 border-teal-500/30",
    iconColor: "text-teal-400",
  },
  amber: {
    gradient: "from-amber-500/10 via-transparent to-transparent",
    border: "border-border/70 hover:border-amber-400/60",
    icon: "bg-amber-500/15 border-amber-500/30",
    iconColor: "text-amber-400",
  },
  emerald: {
    gradient: "from-emerald-500/10 via-transparent to-transparent",
    border: "border-border/70 hover:border-emerald-400/60",
    icon: "bg-emerald-500/15 border-emerald-500/30",
    iconColor: "text-emerald-400",
  },
  pink: {
    gradient: "from-cyan-500/8 via-transparent to-transparent",
    border: "border-border/70 hover:border-cyan-400/60",
    icon: "bg-cyan-500/15 border-cyan-500/30",
    iconColor: "text-cyan-400",
  },
  violet: {
    gradient: "from-indigo-500/10 via-transparent to-transparent",
    border: "border-border/70 hover:border-indigo-400/60",
    icon: "bg-indigo-500/15 border-indigo-500/30",
    iconColor: "text-indigo-400",
  },
};


const agents = [
  {
    id: 0,
    name: "IQVIA Insights",
    desc: "Market intelligence & analysis",
    icon: TrendingUp,
    color: "blue",
  },
  {
    id: 1,
    name: "Exim Trends",
    desc: "Global trade & export-import data",
    icon: Globe,
    color: "teal",
  },
  {
    id: 2,
    name: "Patent Landscape",
    desc: "IP strategy & FTO analysis",
    icon: Shield,
    color: "amber",
  },
  {
    id: 3,
    name: "Clinical Trials",
    desc: "Pipeline & clinical data analysis",
    icon: Activity,
    color: "emerald",
  },
  {
    id: 4,
    name: "Internal Knowledge",
    desc: "Company research & documents",
    icon: BookOpen,
    color: "pink",
  },
  {
    id: 5,
    name: "Web Intelligence",
    desc: "Real-time market insights",
    icon: Globe,
    color: "violet",
  },
];

export function LandingPage({ onSelectFeature, showFullGrid = false, apiError = null }) {
  // Simple features for in-chat view
  const simpleFeatures = [
    { icon: TrendingUp, title: "Market Analysis", desc: "IQVIA insights & data" },
    { icon: Shield, title: "Patent Strategy", desc: "FTO & IP landscape" },
    { icon: Activity, title: "Clinical Trials", desc: "Pipeline analysis" },
  ];

  if (!showFullGrid) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex-1 flex items-center justify-center py-8 px-6 hide-scrollbar overflow-hidden"
      >
        <div className="w-full max-w-2xl dossier-panel rounded-3xl p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 rounded-2xl border border-primary/30 bg-primary/10 flex items-center justify-center">
              <Bot className="text-primary" size={22} />
            </div>
            <div>
              <div className="dossier-label">PharmAssist Briefing</div>
              <h2 className="text-2xl font-display text-foreground">
                What do you want to explore today?
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                Markets, patents, trials, and trade signals in one investigative workflow.
              </p>
            </div>
          </div>

          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-3"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {simpleFeatures.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <motion.button
                  key={idx}
                  type="button"
                  variants={itemVariants}
                  onClick={() => onSelectFeature?.(feature.title)}
                  whileHover={{ y: -3, transition: { duration: 0.2 } }}
                  className="text-left p-4 rounded-2xl border border-border/70 bg-card/60 hover:border-primary/40 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl border border-border/70 bg-secondary/60 flex items-center justify-center">
                      <Icon className="text-primary" size={16} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-foreground">{feature.title}</h3>
                      <p className="text-xs text-muted-foreground">{feature.desc}</p>
                    </div>
                  </div>
                </motion.button>
              );
            })}
          </motion.div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full h-full flex flex-col items-center justify-center px-6 pt-12 pb-10 hide-scrollbar overflow-hidden relative"
    >
      <div className="w-full max-w-6xl relative z-10">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="grid grid-cols-1 lg:grid-cols-[1.05fr_1.3fr] gap-10 items-center"
        >
          <div className="space-y-6">
            <div className="dossier-label">Agentic Portfolio Intelligence</div>
            <motion.h1
              className="text-4xl md:text-6xl font-display text-foreground leading-tight"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              PharmAssist: rapid repurposing intelligence for decisive pipeline bets.
            </motion.h1>
            <motion.p
              className="text-lg text-foreground/70 max-w-xl"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              Move from molecule discovery to differentiated product narratives in hours — with
              synchronized market, trade, patent, clinical, and internal evidence.
            </motion.p>

            {/* <div className="flex flex-wrap items-center gap-3">
              <div className="dossier-chip px-4 py-2 rounded-full text-xs font-semibold">
                6 Specialized Agents
              </div>
              <div className="dossier-chip px-4 py-2 rounded-full text-xs font-semibold">
                Regulatory + Journal + Trial Sources
              </div>
              <div className="dossier-chip px-4 py-2 rounded-full text-xs font-semibold">
                PDF/Excel Report Generator
              </div>
            </div> */}
          </div>

          <div className="dossier-panel rounded-[28px] p-6 md:p-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="dossier-label">Research Lanes</div>
                <h2 className="text-2xl font-display text-foreground">Specialized agent cabinet</h2>
              </div>
              <Zap className="text-primary" size={18} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {agents.map((agent) => {
                const Icon = agent.icon;
                const colors = colorClasses[agent.color];

                return (
                  <motion.div
                    key={agent.id}
                    variants={itemVariants}
                    whileHover={{ y: -4, transition: { duration: 0.2 } }}
                    className={`group relative rounded-2xl border ${colors.border} bg-card/50 p-4 transition-all duration-300`}
                  >
                    <div
                      className={`absolute inset-0 pointer-events-none bg-gradient-to-br ${colors.gradient} opacity-40`}
                    />
                    <div className="relative flex items-start gap-3">
                      <div className={`p-2 rounded-xl border ${colors.icon}`}>
                        <Icon className={colors.iconColor} size={18} />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground text-sm mb-1">
                          {agent.name}
                        </h3>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {agent.desc}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </motion.div>

        {apiError && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 p-3 rounded-xl bg-destructive/10 border border-destructive/30 flex items-center gap-2 max-w-lg"
          >
            <AlertCircle className="text-destructive flex-shrink-0" size={16} />
            <p className="text-xs text-destructive">{apiError}</p>
          </motion.div>
        )}

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="mt-8"
        >
          <motion.p
            className="text-sm text-muted-foreground flex items-center gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.5 }}
          >
            <span className="inline-block w-10 h-px bg-border"></span>
            Start with a molecule, disease, or strategic question below.
          </motion.p>
        </motion.div>
      </div>
    </motion.div>
  );
}
