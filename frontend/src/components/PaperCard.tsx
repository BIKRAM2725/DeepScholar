import { motion } from "framer-motion";
import { ExternalLink, FileText } from "lucide-react";
import type { Paper } from "@/data/mockData";

interface PaperCardProps {
  paper: Paper;
  index: number;
}

const PaperCard = ({ paper, index }: PaperCardProps) => (
  <motion.article
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.3 + index * 0.08, duration: 0.4 }}
    className="glass-card hover-lift group rounded-xl p-5"
  >
    <div className="mb-2 flex items-start gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary/20">
        <FileText className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="text-sm font-semibold leading-snug text-foreground md:text-base">
          {paper.title}
        </h3>
        <p className="mt-1 text-xs text-muted-foreground">
          {paper.authors} · {paper.year}
        </p>
      </div>
    </div>

    <p className="font-serif-reading mb-4 pl-11 text-sm leading-relaxed text-foreground/70">
      {paper.abstract}
    </p>

    <div className="pl-11">
      <a
        href={paper.link}
        target="_blank"
        rel="noopener noreferrer"
        className="group/btn inline-flex items-center gap-1.5 rounded-lg gradient-btn px-3 py-1.5 text-xs font-medium text-primary-foreground transition-all hover:shadow-lg hover:shadow-primary/20"
      >
        View Paper
        <ExternalLink className="h-3 w-3 transition-transform group-hover/btn:translate-x-0.5" />
      </a>
    </div>
  </motion.article>
);

export default PaperCard;
