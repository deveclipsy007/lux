import { sqliteTable, integer, text, index } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";
import { whatsappInstances } from "./instances";
import { agents } from "./agents";

/**
 * Stores inbound and outbound messages exchanged through a WhatsApp instance.
 */
export const messages = sqliteTable(
  "messages",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    instanceId: integer("instance_id")
      .notNull()
      .references(() => whatsappInstances.id, { onDelete: "cascade" }),
    agentId: integer("agent_id")
      .notNull()
      .references(() => agents.id, { onDelete: "cascade" }),
    fromNumber: text("from_number"),
    toNumber: text("to_number"),
    content: text("content"),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`),
    updatedAt: integer("updated_at", { mode: "timestamp" })
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`)
      .$onUpdate(() => sql`CURRENT_TIMESTAMP`),
  },
  (table) => ({
    instanceIdx: index("idx_messages_instance").on(table.instanceId),
    agentIdx: index("idx_messages_agent").on(table.agentId),
  })
);

export type Message = typeof messages.$inferSelect;
