export const papersTable = `
CREATE TABLE IF NOT EXISTS papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
  chat_id UUID REFERENCES chats(id) ON DELETE SET NULL,
  topic TEXT NOT NULL,
  title TEXT,
  mode TEXT NOT NULL DEFAULT 'fast' CHECK (mode IN ('fast','deep')),
  status TEXT NOT NULL DEFAULT 'generating' CHECK (status IN ('generating','ready','failed')),
  storage_path TEXT,
  file_url TEXT,
  sources_used INTEGER,
  error TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
`;