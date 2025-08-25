import type { Config } from "drizzle-kit";
import { config } from "dotenv";

config({ path: ".env" });

export default {
  schema: "./database/schema.ts",
  out: "./database/migrations",
  dialect: "sqlite",
  dbCredentials: {
    url: process.env.DATABASE_URL ?? "sqlite:./data.db",
  },
} satisfies Config;
