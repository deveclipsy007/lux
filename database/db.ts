import { drizzle as drizzleSqlite } from "drizzle-orm/better-sqlite3";
import { drizzle as drizzlePg } from "drizzle-orm/node-postgres";
import Database from "better-sqlite3";
import { Pool } from "pg";
import { config } from "dotenv";

config();

const provider = process.env.DB_PROVIDER ?? "sqlite";
const url =
  process.env.DATABASE_URL ??
  (provider === "sqlite" ? "sqlite:./data.db" : undefined);

let db;

if (provider === "sqlite") {
  const sqlite = new Database(url!.replace(/^sqlite:/, ""));
  db = drizzleSqlite(sqlite);
} else if (provider === "postgres") {
  if (!url) {
    throw new Error("DATABASE_URL is required for Postgres");
  }
  const pool = new Pool({ connectionString: url });
  db = drizzlePg(pool);
} else {
  throw new Error(`Unsupported DB_PROVIDER: ${provider}`);
}

export { db };
export default db;
