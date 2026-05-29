import express from "express";
import { syncUser,logoutUser } from "../controllers/auth.controller.ts";
import { requireAuth } from "../middleware/auth.middleware.ts";

const router = express.Router();

router.post("/sync", requireAuth, syncUser);
router.post("/logout", requireAuth, logoutUser);
export default router;