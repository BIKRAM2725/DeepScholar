import express from "express";
import { requireAuth } from "../middleware/auth.middleware.ts";
import {
  deletePaperHandler,
  generatePaperHandler,
  getPaperHandler,
  listPapersHandler,
} from "../controllers/paper.controller.ts";

const router = express.Router();

// Figures travel as base64 in the body, so this route needs a bigger limit
// than the app's default JSON body parser.
router.post("/generate", express.json({ limit: "30mb" }), requireAuth, generatePaperHandler);
router.get("/", requireAuth, listPapersHandler);
router.get("/:id", requireAuth, getPaperHandler);
router.delete("/:id", requireAuth, deletePaperHandler);

export default router;