
import { db } from "../index.js";

export const createMessage = async (
  chatId: string,
  role: "user" | "assistant",
  content: string
) => {
  const { rows } = await db.query(
    `INSERT INTO messages (chat_id, role, content) VALUES ($1,$2,$3) RETURNING *`,
    [chatId, role, content]
  );
  return rows[0];
};

export const getMessages = async (chatId: string, limit = 10) => {
  const { rows } = await db.query(
    `SELECT * FROM messages WHERE chat_id = $1 ORDER BY created_at DESC LIMIT $2`,
    [chatId, limit]
  );
  return rows.reverse().map((row: any) => `${row.role}: ${row.content}`);
};