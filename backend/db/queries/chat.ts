
import { db } from "../index.js";

export const createChat = async (userId: string, title = "New Chat") => {
  const { rows } = await db.query(
    `INSERT INTO chats (user_id, title) VALUES ($1, $2) RETURNING *`,
    [userId, title]
  );
  return rows[0];
};

export const getUserChats = async (userId: string) => {
  const { rows } = await db.query(
    `SELECT * FROM chats WHERE user_id = $1 ORDER BY created_at DESC`,
    [userId]
  );
  return rows;
};

export const getChatById = async (chatId: string) => {
  const { rows } = await db.query(
    `SELECT * FROM chats WHERE id = $1`,
    [chatId]
  );
  return rows[0];
};
export const deleteChat = async (chatId: string) => {
  const { rowCount } = await db.query(
    `DELETE FROM chats WHERE id = $1`,
    [chatId]
  );
  return rowCount;
};