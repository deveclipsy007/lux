import { sqliteTable, integer, text, index } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";
import { agents } from "./agents";
import { whatsappInstances } from "./instances";

/**
 * Generic system event log for auditing and debugging.
 */
export const systemEvents = sqliteTable(
  "system_events",
  {
    id: integer("id").primaryKey({ autoIncrement: true }),
    eventType: text("event_type").notNull(),
    source: text("source"),
    agentId: integer("agent_id").references(() => agents.id, {
      onDelete: "set null",
    }),
    instanceId: integer("instance_id").references(
      () => whatsappInstances.id,
      { onDelete: "set null" }
    ),
    data: text("data"),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`),
    updatedAt: integer("updated_at", { mode: "timestamp" })
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`)
      .$onUpdate(() => sql`CURRENT_TIMESTAMP`),
  },
  (table) => ({
    typeIdx: index("idx_system_events_type").on(table.eventType),
  })
);

export type SystemEvent = typeof systemEvents.$inferSelect;
