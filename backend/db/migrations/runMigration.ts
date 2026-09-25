// runMigration.ts

import { runMigrations } from "./001_init.ts";

async function main() {
  try {
    await runMigrations();
    console.log("Migrations done");
    process.exit(0);
  } catch (error) {
    console.error("Migration failed:", error);
    process.exit(1);
  }
}

main();