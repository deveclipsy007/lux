import type { Config } from "drizzle-kit";
import { config } from "dotenv";

config({ path: ".env" });

const provider = process.env.DB_PROVIDER ?? "sqlite";
const dialect = provider === "postgres" ? "postgresql" : "sqlite";
const rawUrl = process.env.DATABASE_URL;
const url =
  provider === "sqlite"
    ? rawUrl?.replace(/^sqlite:/, "") ?? "./data.db"
    : rawUrl;

if (provider === "postgres" && !url) {
  throw new Error("DATABASE_URL is required when DB_PROVIDER=postgres");
}

export default {
  schema: "./database/schema/index.ts",
  out: "./database/migrations",
  dialect,
  dbCredentials: {
    url,
  },
} satisfies Config;
