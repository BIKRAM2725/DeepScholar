import { db } from "../index.js";

// 1. Define an interface for the expected arguments
interface CreateUserParams {
  id: string;
  email?: string | null;
  name?: string | null;
}

/**
 * createUser({ id, email, name })
 * - inserts or upserts a user record based on Clerk userId
 */
export const createUser = async ({ id, email = null, name = null }: CreateUserParams) => {
  if (!id) throw new Error("createUser: missing id");
  const query = `
    INSERT INTO users (id, name, email)
    VALUES ($1, $2, $3)
    ON CONFLICT (id) DO UPDATE
      SET name  = COALESCE(EXCLUDED.name, users.name),
          email = COALESCE(EXCLUDED.email, users.email)
    RETURNING *;
  `;
  const { rows } = await db.query(query, [id, name, email]);
  return rows[0];
};


export const getUserById = async (id: string) => {
  const { rows } = await db.query(`SELECT * FROM users WHERE id = $1`, [id]);
  return rows[0] || null;
};