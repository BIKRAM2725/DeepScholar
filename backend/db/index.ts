import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import pkg from "pg";

// Recreate __dirname for ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load the .env file exactly two levels up (from /db to /backend root)
// Load the .env file exactly ONE level up (from /db to /backend root)
dotenv.config({ path: path.resolve(__dirname, "../.env") });

const { Pool } = pkg;

export const db = new Pool({
  connectionString: process.env.DATABASE_URL,
});