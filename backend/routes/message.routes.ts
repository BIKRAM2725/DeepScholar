import express from "express";
import { requireAuth } from "../middleware/auth.middleware.ts";
import { getMessagesHandler, sendMessageHandler } from "../controllers/message.controller.ts";

const router = express.Router();

router.get("/:id/messages", requireAuth, getMessagesHandler);
router.post("/:id/messages", requireAuth, sendMessageHandler);

export default router;