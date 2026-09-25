import { db } from "../index.js";

export const createPaper = async (
  userId,
  topic,
  mode,
  chatId = null
) => {
  const { rows } = await db.query(
    `INSERT INTO papers (user_id, topic, mode, chat_id, status)
     VALUES ($1, $2, $3, $4, 'generating')
     RETURNING *`,
    [userId, topic, mode, chatId]
  );

  return rows[0];
};

export const markPaperReady = async (
  id,
  fields
) => {
  const { rows } = await db.query(
    `UPDATE papers
     SET status = 'ready',
         title = $2,
         storage_path = $3,
         file_url = $4,
         sources_used = $5,
         updated_at = NOW()
     WHERE id = $1
     RETURNING *`,
    [
      id,
      fields.title,
      fields.storagePath,
      fields.fileUrl,
      fields.sourcesUsed,
    ]
  );

  return rows[0];
};

export const markPaperFailed = async (id, error) => {
  const { rows } = await db.query(
    `UPDATE papers
     SET status = 'failed',
         error = $2,
         updated_at = NOW()
     WHERE id = $1
     RETURNING *`,
    [id, String(error).slice(0, 500)]
  );

  return rows[0];
};

export const getUserPapers = async (userId) => {
  const { rows } = await db.query(
    `SELECT *
     FROM papers
     WHERE user_id = $1
     ORDER BY created_at DESC
     LIMIT 100`,
    [userId]
  );

  return rows;
};

export const getPaperById = async (id) => {
  const { rows } = await db.query(
    `SELECT *
     FROM papers
     WHERE id = $1`,
    [id]
  );

  return rows[0];
};

export const deletePaper = async (id) => {
  const { rowCount } = await db.query(
    `DELETE FROM papers
     WHERE id = $1`,
    [id]
  );

  return rowCount ?? 0;
};