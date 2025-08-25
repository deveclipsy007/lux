import { sqliteTable, integer, text, index } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";
import { agents } from "./agents";

/**
 * Tracks WhatsApp Web instances associated with an agent.
 */
export const whatsappInstances = sqliteTable(
  "whatsapp_instances",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    agentId: integer("agent_id")
      .notNull()
      .references(() => agents.id, { onDelete: "cascade" }),
    status: text("status").notNull().default("inactive"),
    qrCode: text("qr_code"),
    phoneNumber: text("phone_number"),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`),
    updatedAt: integer("updated_at", { mode: "timestamp" })
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`)
      .$onUpdate(() => sql`CURRENT_TIMESTAMP`),
  },
  (table) => ({
    agentIdx: index("idx_whatsapp_instances_agent").on(table.agentId),
  })
);

export type WhatsappInstance = typeof whatsappInstances.$inferSelect;
