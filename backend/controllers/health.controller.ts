import { Request, Response } from "express";

export const healthCheck = async (req: Request, res: Response) => {
  try {
    const health = {
      status: "ok",
      timestamp: new Date().toISOString(),
      services: {
        backend: "ok",
        database: "unknown",
        rag: "unknown"
      }
    };

    // Check database
    try {
      const { db } = await import("../db/index.js");
      await db.query("SELECT 1");
      health.services.database = "ok";
    } catch (err) {
      health.services.database = "error";
      health.status = "degraded";
    }

    // Check RAG system
    try {
      const pythonApiUrl = process.env.ORCHESTRATOR_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${pythonApiUrl}/docs`, { method: "HEAD" });
      health.services.rag = response.ok ? "ok" : "error";
    } catch (err) {
      health.services.rag = "error";
      health.status = "degraded";
    }

    const statusCode = health.status === "ok" ? 200 : 503;
    res.status(statusCode).json(health);
  } catch (err) {
    console.error("[Health Check Error]", err);
    res.status(500).json({
      status: "error",
      timestamp: new Date().toISOString(),
      error: "Health check failed"
    });
  }
};
