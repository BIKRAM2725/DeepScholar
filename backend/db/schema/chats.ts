export const chatsTable = `
CREATE TABLE IF NOT EXISTS chats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
  title TEXT,                  
  created_at TIMESTAMP DEFAULT NOW()
);
`;