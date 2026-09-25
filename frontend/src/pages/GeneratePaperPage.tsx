import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@clerk/clerk-react";
import { FileText, Loader2, Rocket, Telescope, ExternalLink, Trash2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import AnimatedBackground from "@/components/AnimatedBackground";
import { api, type Paper, type PaperMode, type PaperStreamEvent } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface GeneratePaperPageProps {
  darkMode: boolean;
  onToggleDark: () => void;
}

const MODES: { value: PaperMode; label: string; desc: string; icon: typeof Rocket }[] = [
  { value: "fast", label: "Fast", desc: "Web search only. Ready in about a minute.", icon: Rocket },
  { value: "deep", label: "Deep Research", desc: "Combines your indexed corpus (FAISS) with web search.", icon: Telescope },
];

function parseMetrics(text: string) {
  const metrics: Record<string, number> = {};
  const bad: string[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const m = line.match(/^(.+?)\s*[:=]\s*(-?\d+(?:\.\d+)?)$/);
    if (m) metrics[m[1].trim()] = Number(m[2]);
    else bad.push(line);
  }
  return { metrics, bad };
}

const GeneratePaperPage = ({ darkMode, onToggleDark }: GeneratePaperPageProps) => {
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const { toast } = useToast();

  const [topic, setTopic] = useState("");
  const [authors, setAuthors] = useState("");
  const [notes, setNotes] = useState("");
  const [steps, setSteps] = useState("");
  const [metricsText, setMetricsText] = useState("");
  const [mode, setMode] = useState<PaperMode>("fast");

  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState<{ step: string; index: number; total: number } | null>(null);
  const [error, setError] = useState("");

  const [papers, setPapers] = useState<Paper[]>([]);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const abortRef = useRef<{ abort: () => void } | null>(null);

  const isOriginal = Boolean(notes.trim() || metricsText.trim());

  const loadPapers = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      setPapers(await api.getPapers(token));
    } catch (err) {
      console.error("Failed to load papers:", err);
    } finally {
      setLoadingPapers(false);
    }
  };

  useEffect(() => {
    loadPapers();
    return () => abortRef.current?.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onGenerate = async () => {
    if (!topic.trim() || generating) return;

    const { metrics, bad } = parseMetrics(metricsText);
    if (bad.length) {
      setError(`Write each result as name = value. Fix: ${bad.join("; ")}`);
      return;
    }

    setError("");
    setGenerating(true);
    setProgress({ step: "Starting…", index: 0, total: 1 });

    const token = await getToken();
    if (!token) {
      setGenerating(false);
      navigate("/");
      return;
    }

    abortRef.current = api.generatePaperStream(
      token,
      {
        topic: topic.trim(),
        authors: authors.trim() || "Author Name",
        notes: notes.trim(),
        steps: steps.split("\n").map((s) => s.trim()).filter(Boolean),
        metrics,
        mode,
      },
      (event: PaperStreamEvent) => {
        if (event.type === "progress") {
          setProgress({ step: event.step, index: event.index, total: event.total });
        } else if (event.type === "error") {
          setError(event.message);
          setGenerating(false);
        } else if (event.type === "done") {
          setGenerating(false);
          setProgress(null);
          setPapers((prev) => [event.paper, ...prev]);
          toast({ title: "Paper ready", description: event.paper.title ?? topic });
        }
      },
      (message) => {
        setError(message);
        setGenerating(false);
      }
    );
  };

  const onDelete = async (id: string) => {
    try {
      const token = await getToken();
      if (!token) return;
      await api.deletePaper(token, id);
      setPapers((prev) => prev.filter((p) => p.id !== id));
    } catch {
      toast({ title: "Error", description: "Could not delete the paper.", variant: "destructive" });
    }
  };

  return (
    <div className="relative min-h-screen">
      <AnimatedBackground />
      <Navbar darkMode={darkMode} onToggleDark={onToggleDark} />

      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-4 py-10 md:px-6">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h1 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">Generate a paper</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            An IEEE-formatted PDF, built section by section from real sources.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="glass-card glow-border rounded-xl p-5 md:p-6"
        >
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Topic</label>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="YOLOv11 tomato leaf disease detection"
            className="mb-4 w-full rounded-lg border border-border bg-secondary/40 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary"
          />

          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Search mode</label>
          <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {MODES.map(({ value, label, desc, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => setMode(value)}
                className={`flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-left transition-colors ${
                  mode === value ? "border-primary bg-primary/10" : "border-border hover:bg-secondary/40"
                }`}
              >
                <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${mode === value ? "text-primary" : "text-muted-foreground"}`} />
                <span>
                  <span className="block text-sm font-medium text-foreground">{label}</span>
                  <span className="block text-xs text-muted-foreground">{desc}</span>
                </span>
              </button>
            ))}
          </div>

          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Authors (optional)</label>
          <input
            value={authors}
            onChange={(e) => setAuthors(e.target.value)}
            placeholder="Your Name, Your University"
            className="mb-4 w-full rounded-lg border border-border bg-secondary/40 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary"
          />

          <p className="mb-4 rounded-lg border-l-2 border-primary/60 bg-secondary/30 px-3 py-2 text-xs text-muted-foreground">
            {isOriginal
              ? "Original work: the method and results use only what you enter below."
              : "Literature review: with no notes or results, the paper only summarizes published work."}
          </p>

          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Your notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={4}
            placeholder="Dataset, model, training setup, findings."
            className="mb-4 w-full resize-y rounded-lg border border-border bg-secondary/40 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary"
          />

          <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Pipeline steps (optional)</label>
              <textarea
                value={steps}
                onChange={(e) => setSteps(e.target.value)}
                rows={4}
                placeholder={"Image acquisition\nPreprocessing\nModel training\nEvaluation"}
                className="w-full resize-y rounded-lg border border-border bg-secondary/40 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Results (optional)</label>
              <textarea
                value={metricsText}
                onChange={(e) => setMetricsText(e.target.value)}
                rows={4}
                placeholder={"Precision = 0.91\nRecall = 0.88\nmAP50 = 0.93"}
                className="w-full resize-y rounded-lg border border-border bg-secondary/40 px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>

          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}

          <button
            onClick={onGenerate}
            disabled={generating || !topic.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-lg gradient-btn px-4 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:shadow-lg hover:shadow-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
            {generating ? "Writing your paper…" : "Generate PDF"}
          </button>

          {generating && progress && (
            <div className="mt-4">
              <div className="mb-1.5 flex justify-between text-xs text-muted-foreground">
                <span>{progress.step}</span>
                <span>{progress.index}/{progress.total}</span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                <motion.div
                  className="h-full gradient-btn"
                  animate={{ width: `${Math.min(100, (progress.index / Math.max(progress.total, 1)) * 100)}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">Usually takes 1 to 3 minutes. Keep this tab open.</p>
            </div>
          )}
        </motion.div>

        <div>
          <h2 className="mb-3 text-sm font-semibold text-foreground">Your papers</h2>
          {loadingPapers ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : papers.length === 0 ? (
            <p className="text-sm text-muted-foreground">No papers yet. Generate one above.</p>
          ) : (
            <div className="flex flex-col gap-2">
              <AnimatePresence>
                {papers.map((paper) => (
                  <motion.div
                    key={paper.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="glass-card hover-lift flex items-center justify-between gap-3 rounded-lg px-4 py-3"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">{paper.title || paper.topic}</p>
                      <p className="text-xs text-muted-foreground">
                        {paper.mode === "deep" ? "Deep research" : "Fast"}
                        {paper.sources_used ? ` · ${paper.sources_used} sources` : ""}
                        {" · "}
                        {paper.status === "generating" ? "generating…" : paper.status === "failed" ? "failed" : new Date(paper.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-1">
                      {paper.status === "ready" && paper.file_url && (
                        <a
                          href={paper.file_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                          aria-label="Open PDF"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                      <button
                        onClick={() => onDelete(paper.id)}
                        className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-destructive"
                        aria-label="Delete paper"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GeneratePaperPage;