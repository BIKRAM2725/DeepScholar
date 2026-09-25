import type { Request, Response } from "express";
import { createPaper, deletePaper, getPaperById, getUserPapers, markPaperFailed, markPaperReady } from "../db/queries/paper.js";
import { uploadPaperPdf } from "../lib/supabase.js";

const RAG_URL = process.env.RAG_URL ?? "http://127.0.0.1:8000";
const STREAM_TIMEOUT_MS = 6 * 60 * 1000; // generation can take a few minutes

function sse(res: Response, event: Record<string, unknown>) {
  res.write(`data: ${JSON.stringify(event)}\n\n`);
}


export const generatePaperHandler = async (req: Request, res: Response) => {
  if (!req.user) return res.status(401).json({ error: "Unauthorized" });
  const userId = req.user.sub;

  const topic = typeof req.body?.topic === "string" ? req.body.topic.trim() : "";
  if (!topic) return res.status(400).json({ error: "Enter a topic for the paper." });

  const mode: "fast" | "deep" = req.body?.mode === "deep" ? "deep" : "fast";
  const chatId = typeof req.body?.chatId === "string" ? req.body.chatId : null;

  let paper;
  try {
    paper = await createPaper(userId, topic, mode, chatId);
  } catch (err) {
    console.error("[papers] failed to create row:", err);
    return res.status(500).json({ error: "Could not start paper generation." });
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();
  sse(res, { type: "started", paperId: paper.id });

  let finished = false;
  const finish = async (fail?: string) => {
    if (finished) return;
    finished = true;
    if (fail) {
      await markPaperFailed(paper.id, fail).catch((e) => console.error("[papers] markPaperFailed:", e));
    }
    res.end();
  };

  req.on("close", () => {
    if (!finished) finish("Client disconnected before generation finished.");
  });

  let upstream: globalThis.Response;
  try {
    upstream = await fetch(`${RAG_URL}/generate-paper/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
      signal: AbortSignal.timeout(STREAM_TIMEOUT_MS),
    });
  } catch (err) {
    console.error("[papers] could not reach RAG service:", err);
    sse(res, { type: "error", message: "The paper service is not reachable. Start the RAG server on port 8000." });
    return finish("RAG service unreachable.");
  }

  if (!upstream.ok || !upstream.body) {
    sse(res, { type: "error", message: `The paper service returned an error (${upstream.status}).` });
    return finish(`Upstream HTTP ${upstream.status}`);
  }

  const reader = upstream.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const raw = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        const line = raw.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;

        let evt: any;
        try {
          evt = JSON.parse(line.slice(6));
        } catch {
          continue;
        }

        if (evt.type === "progress") {
          sse(res, evt);
        } else if (evt.type === "error") {
          sse(res, evt);
          await finish(evt.message || "Paper generation failed.");
          return;
        } else if (evt.type === "done") {
          try {
            const pdf = Buffer.from(evt.pdf_base64 as string, "base64");
            const { path, url } = await uploadPaperPdf(userId, paper.id, pdf);
            const saved = await markPaperReady(paper.id, {
              title: evt.title,
              storagePath: path,
              fileUrl: url,
              sourcesUsed: evt.sources_used ?? 0,
            });
            sse(res, { type: "done", paper: saved });
          } catch (err) {
            console.error("[papers] upload/save failed:", err);
            sse(res, { type: "error", message: "The paper was generated but could not be saved." });
            await finish("Upload or database save failed.");
            return;
          }
          await finish();
          return;
        }
      }
    }
    await finish("Generation ended unexpectedly.");
  } catch (err) {
    console.error("[papers] stream error:", err);
    sse(res, { type: "error", message: "Paper generation was interrupted." });
    await finish(err instanceof Error ? err.message : "Stream error.");
  }
};

export const listPapersHandler = async (req: Request, res: Response) => {
  if (!req.user) return res.status(401).json({ error: "Unauthorized" });
  try {
    res.json(await getUserPapers(req.user.sub));
  } catch (err) {
    console.error("[papers] list failed:", err);
    res.status(500).json({ error: "Could not load papers." });
  }
};

export const getPaperHandler = async (req: Request, res: Response) => {
  if (!req.user) return res.status(401).json({ error: "Unauthorized" });
  const { id } = req.params as { id: string };
  try {
    const paper = await getPaperById(id);
    if (!paper || paper.user_id !== req.user.sub) {
      return res.status(404).json({ error: "Paper not found" });
    }
    res.json(paper);
  } catch (err) {
    console.error("[papers] get failed:", err);
    res.status(500).json({ error: "Could not load paper." });
  }
};

export const deletePaperHandler = async (req: Request, res: Response) => {
  if (!req.user) return res.status(401).json({ error: "Unauthorized" });
  const { id } = req.params as { id: string };
  try {
    const paper = await getPaperById(id);
    if (!paper || paper.user_id !== req.user.sub) {
      return res.status(404).json({ error: "Paper not found" });
    }
    await deletePaper(id);
    res.json({ success: true });
  } catch (err) {
    console.error("[papers] delete failed:", err);
    res.status(500).json({ error: "Could not delete paper." });
  }
};