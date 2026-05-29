import { verifyToken } from "@clerk/backend";

import type { Request, Response, NextFunction } from "express"; 
if (!process.env.CLERK_SECRET_KEY) {
  throw new Error("CLERK_SECRET_KEY is not set");
}

export const requireAuth = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith("Bearer ")) {
      return res.status(401).json({ error: "Unauthorized" });
    }

    const token = authHeader.split(" ")[1];
    if (!token) {
      return res.status(401).json({ error: "Unauthorized" });
    }

    const payload = await verifyToken(token, {
      secretKey: process.env.CLERK_SECRET_KEY,
    });

    req.user = payload;
    next();

  } catch (err) {
    console.error("[requireAuth] Unexpected error:", err);
    return res.status(401).json({ error: "Unauthorized" });
  }
};