import { Request, Response } from "express";
import { createUser } from "../db/queries/user.js";
import { clerkClient } from '@clerk/clerk-sdk-node';
export const syncUser = async (req: Request, res: Response) => {
  try {
   
    if (!req.user) return res.status(401).json({ error: "No user found" });
    
    const { sub: id, email, name } = req.user;

    await createUser({
      id,
      email: email || null,
      name: name || null,
    });

    res.json({ success: true });
  } catch (error) {
    console.error("[syncUser error]", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
};

export const logoutUser = async (req: Request, res: Response) => {
  try {
    if (!req.user || !req.user.sid) {
      return res.status(401).json({ error: "Session missing or user unauthenticated" });
    }

    // `sid` from the JWT payload corresponds to the Clerk Session ID
    const sessionId = req.user.sid; 

    // Revoke the active session via the Clerk Backend API
    await clerkClient.sessions.revokeSession(sessionId);

    res.json({ success: true, message: "Session successfully revoked in Clerk" });
  } catch (error) {
    console.error("[logoutUser error]", error);
    res.status(500).json({ error: "Failed to revoke session" });
  }
};