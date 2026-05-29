
import { Request, Response } from "express";
import { createChat, getUserChats , getChatById, deleteChat} from "../db/queries/chat.js";

export const createChatHandler = async (req: Request, res: Response) => {
  try {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });

    const chat = await createChat(req.user.sub);
    res.json(chat);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Internal error" });
  }
};

export const getChatsHandler = async (req: Request, res: Response) => {
  try {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });
    const chats = await getUserChats(req.user.sub);
    res.json(chats);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Internal error" });
  }
};
export const deleteChatHandler = async (req: Request, res: Response) => {
  try {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });

    const { id: chatId } = req.params as { id: string };

    // Verify the chat exists and belongs to the user
    const chat = await getChatById(chatId);
    
    if (!chat) {
      return res.status(404).json({ error: "Chat not found" });
    }
    
    if (chat.user_id !== req.user.sub) {
      return res.status(403).json({ error: "Forbidden" });
    }

    const rowCount = await deleteChat(chatId);
    
    if (rowCount === 0) {
      return res.status(500).json({ error: "Failed to delete chat" });
    }

    res.json({ success: true, message: "Chat deleted" });
  } catch (err) {
    console.error("[deleteChatHandler error]", err);
    res.status(500).json({ error: "Internal error" });
  }
};