import { motion } from "framer-motion";
import { Check, Loader2, Database, FileSearch, Brain, Sparkles, BarChart3, Zap } from "lucide-react";
import { useEffect, useState } from "react";

const steps = [
  { label: "Searching academic databases", icon: Database },
  { label: "Finding high quality research papers", icon: FileSearch },
  { label: "Analyzing paper abstracts", icon: Brain },
  { label: "Generating concise summary", icon: Sparkles },
  { label: "Ranking most relevant papers", icon: BarChart3 },
  { label: "Preparing final insights", icon: Zap },
];

interface LoadingStepsProps {
  onComplete: () => void;
}

const LoadingSteps = ({ onComplete }: LoadingStepsProps) => {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (activeStep >= steps.length) {
      const t = setTimeout(onComplete, 500);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setActiveStep((s) => s + 1), 650);
    return () => clearTimeout(t);
  }, [activeStep, onComplete]);

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-4">
      <div className="w-full max-w-lg">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center"
        >
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl gradient-btn animate-pulse_glow">
            <Sparkles className="h-5 w-5 text-primary-foreground" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">
            AI is analyzing your query…
          </p>
        </motion.div>

        <div className="space-y-2">
          {steps.map((step, i) => {
            const done = i < activeStep;
            const current = i === activeStep;
            const Icon = step.icon;
            return (
              <motion.div
                key={step.label}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: i <= activeStep ? 1 : 0.25, x: 0 }}
                transition={{ delay: i * 0.08, duration: 0.3 }}
                className={`glass-card flex items-center gap-3 rounded-lg px-4 py-3 transition-all duration-300 ${
                  current ? "glow-border-strong" : done ? "border-primary/20" : ""
                }`}
              >
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors ${
                  done ? "bg-primary/15 text-primary" : current ? "gradient-btn text-primary-foreground" : "bg-secondary text-muted-foreground"
                }`}>
                  {done ? (
                    <Check className="h-4 w-4" />
                  ) : current ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </div>
                <span className={`text-sm ${done || current ? "text-foreground font-medium" : "text-muted-foreground"}`}>
                  {step.label}
                </span>
              </motion.div>
            );
          })}
        </div>

        {/* Skeleton cards */}
        <div className="mt-10 space-y-3">
          {[1, 2, 3].map((i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              transition={{ delay: 0.8 + i * 0.2 }}
              className="glass-card rounded-xl p-5"
            >
              <div className="mb-3 h-4 w-3/4 rounded-md bg-muted animate-pulse" />
              <div className="mb-4 h-3 w-2/5 rounded-md bg-muted/70 animate-pulse" />
              <div className="space-y-2">
                <div className="h-3 w-full rounded-md bg-muted/50 animate-pulse" />
                <div className="h-3 w-5/6 rounded-md bg-muted/50 animate-pulse" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LoadingSteps;
