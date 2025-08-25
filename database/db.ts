import { drizzle } from "drizzle-orm/better-sqlite3";
import Database from "better-sqlite3";
import { config } from "dotenv";

config();

const provider = process.env.DB_PROVIDER ?? "sqlite";
const url = process.env.DATABASE_URL ?? "sqlite:./data.db";

if (provider !== "sqlite") {
  throw new Error(`Unsupported DB_PROVIDER: ${provider}`);
}

const sqlite = new Database(url.replace(/^sqlite:/, ""));
export const db = drizzle(sqlite);

export default db;
