import { db } from "../index.ts";
import { usersTable } from "../schema/users.ts";
import { chatsTable } from "../schema/chats.ts";
import { messagesTable } from "../schema/messages.ts";

export const runMigrations = async () => {
  await db.query(usersTable);
  await db.query(chatsTable);
  await db.query(messagesTable);

  await db.query(`CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id)`);
  await db.query(`CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)`);
  await db.query(`CREATE INDEX IF NOT EXISTS idx_messages_chat_time ON messages(chat_id, created_at)`);
};