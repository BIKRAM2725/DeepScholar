import { Request, Response } from "express";
import { getChatById } from "../db/queries/chat.js";
import { createMessage, getMessages } from "../db/queries/message.js";

export const getMessagesHandler = async (req: Request, res: Response) => {
  try {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });
    const { id: chatId } = req.params as { id: string };
    const chat = await getChatById(chatId);
    if (!chat || chat.user_id !== req.user.sub) {
      return res.status(403).json({ error: "Forbidden" });
    }
    const messages = await getMessages(chatId, 10);
    res.json(messages);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Internal error" });
  }
};
export const sendMessageHandler = async (req: Request, res: Response) => {
  try {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });
    const { id: chatId } = req.params as { id: string };
    const { query, mode } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: "Query is required" });
    }
    
    const chat = await getChatById(chatId);
    if (!chat || chat.user_id !== req.user.sub) {
      return res.status(403).json({ error: "Forbidden" });
    }
    
    // Save user message
    await createMessage(chatId, "user", query);

    // Get message history and format for RAG system
    const messages = await getMessages(chatId, 10);
    
    // Format history as array of strings (alternating user/assistant messages)
    const history = messages.map(msg => `${msg.role}: ${msg.content}`);

    const pythonApiUrl = process.env.ORCHESTRATOR_URL || "http://127.0.0.1:8000";
    
    const endpointMap: Record<string, string> = {
      query: "query",
      chatllm: "chatllm",
    };

    const endpoint = endpointMap[mode] || "chatllm";

    console.log(`[Backend] Sending request to RAG system: ${pythonApiUrl}/${endpoint}`);
    console.log(`[Backend] Query: ${query}`);
    console.log(`[Backend] History length: ${history.length}`);

    let orchestratorRes;
    try {
      orchestratorRes = await fetch(`${pythonApiUrl}/${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          history: history
        }),
      });
    } catch (fetchError) {
      console.error("[Backend] Failed to connect to RAG system:", fetchError);
      return res.status(503).json({ 
        error: "RAG system unavailable",
        details: "Could not connect to the AI service. Please ensure the RAG system is running on port 8000."
      });
    }

    if (!orchestratorRes.ok) {
      const errorDetails = await orchestratorRes.text();
      console.error(`[Backend] RAG system error (${orchestratorRes.status}):`, errorDetails);
      
      return res.status(502).json({ 
        error: "RAG system error",
        details: `The AI service returned an error: ${orchestratorRes.status}`,
        message: errorDetails
      });
    }

    const data = await orchestratorRes.json();
    const response = data.answer;

    console.log("[Backend] RAG response data:", JSON.stringify(data).substring(0, 200));
    console.log("[Backend] Extracted response type:", typeof response);
    console.log("[Backend] Extracted response preview:", typeof response === 'string' ? response.substring(0, 100) : response);

    if (!response) {
      console.error("[Backend] No answer in RAG response:", data);
      return res.status(500).json({ error: "Invalid response from RAG system" });
    }

    // Save assistant response
    await createMessage(chatId, "assistant", response);
    
    console.log("[Backend] Successfully processed query");
    console.log("[Backend] Returning response type:", typeof response);
    res.json({ response });

  } catch (err) {
    console.error("[Backend] Unexpected error in sendMessageHandler:", err);
    res.status(500).json({ 
      error: "Internal error",
      details: err instanceof Error ? err.message : "Unknown error"
    });
  }
};