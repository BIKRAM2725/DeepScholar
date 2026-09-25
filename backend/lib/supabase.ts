// backend/lib/supabase.ts
import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  throw new Error(
    "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set (server-side service " +
      "role key, never the anon key — this client uploads on the user's behalf)."
  );
}

// Service-role client: bypasses row-level security, so it must only ever be
// used from the backend, never shipped to the frontend.
export const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

export const PAPERS_BUCKET = process.env.SUPABASE_PAPERS_BUCKET || "papers";

/** Uploads a generated paper PDF and returns its storage path + public URL. */
export async function uploadPaperPdf(
  userId: string,
  paperId: string,
  pdf: Buffer
): Promise<{ path: string; url: string }> {
  const path = `${userId}/${paperId}.pdf`;

  const { error } = await supabase.storage.from(PAPERS_BUCKET).upload(path, pdf, {
    contentType: "application/pdf",
    upsert: true,
  });
  if (error) throw new Error(`Supabase upload failed: ${error.message}`);

  const { data } = supabase.storage.from(PAPERS_BUCKET).getPublicUrl(path);
  return { path, url: data.publicUrl };
}

/** For a private bucket, call this instead to hand the frontend a time-limited link. */
export async function signPaperUrl(path: string, expiresInSeconds = 3600) {
  const { data, error } = await supabase.storage
    .from(PAPERS_BUCKET)
    .createSignedUrl(path, expiresInSeconds);
  if (error) throw new Error(`Supabase sign failed: ${error.message}`);
  return data.signedUrl;
}