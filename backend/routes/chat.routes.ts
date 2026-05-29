// routes/chat.routes.ts
import express from "express";
import { requireAuth } from "../middleware/auth.middleware.ts";
import { createChatHandler, getChatsHandler, deleteChatHandler  } from "../controllers/chat.controller.ts";

const router = express.Router();

router.get("/", requireAuth, getChatsHandler);
router.post("/", requireAuth, createChatHandler);
router.delete("/:id", requireAuth, deleteChatHandler);
export default router;