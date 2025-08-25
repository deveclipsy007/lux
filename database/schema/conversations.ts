import { sqliteTable, integer, text, index } from "drizzle-orm/sqlite-core";
import { sql } from "drizzle-orm";
import { whatsappInstances } from "./instances";
import { agents } from "./agents";

/**
 * Represents a chat between the agent and a contact on a specific instance.
 */
export const conversations = sqliteTable(
  "conversations",
  {
    chatId: text("chat_id").primaryKey(),
    instanceId: integer("instance_id")
      .notNull()
      .references(() => whatsappInstances.id, { onDelete: "cascade" }),
    agentId: integer("agent_id")
      .notNull()
      .references(() => agents.id, { onDelete: "cascade" }),
    contactNumber: text("contact_number").notNull(),
    createdAt: integer("created_at", { mode: "timestamp" })
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`),
    updatedAt: integer("updated_at", { mode: "timestamp" })
      .notNull()
      .default(sql`CURRENT_TIMESTAMP`)
      .$onUpdate(() => sql`CURRENT_TIMESTAMP`),
  },
  (table) => ({
    instanceIdx: index("idx_conversations_instance").on(table.instanceId),
    agentIdx: index("idx_conversations_agent").on(table.agentId),
  })
);

export type Conversation = typeof conversations.$inferSelect;
