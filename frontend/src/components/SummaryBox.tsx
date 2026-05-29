import { motion } from "framer-motion";
import { Sparkles, Copy, Check } from "lucide-react";
import { useState } from "react";

interface SummaryBoxProps {
  summary: string;
  keyPoints: string[];
}

const SummaryBox = ({ summary, keyPoints }: SummaryBoxProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card glow-border rounded-xl p-6"
      style={{ background: "hsl(var(--summary-bg))" }}
    >
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md gradient-btn">
            <Sparkles className="h-3 w-3 text-primary-foreground" />
          </div>
          <span className="text-xs font-semibold uppercase tracking-wider text-primary">
            AI-Generated Summary
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      <p className="font-serif-reading text-base leading-[1.7] text-foreground/90">
        {summary}
      </p>

      <div className="mt-6">
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-foreground/70">
          Key Insights
        </h3>
        <div className="space-y-2">
          {keyPoints.map((point, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.1 }}
              className="flex gap-3 rounded-lg bg-secondary/50 px-4 py-3"
            >
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-primary/15 text-[10px] font-bold text-primary">
                {i + 1}
              </span>
              <span className="font-serif-reading text-sm leading-relaxed text-foreground/85">
                {point}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default SummaryBox;
