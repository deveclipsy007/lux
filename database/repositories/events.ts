import { eq, sql } from "drizzle-orm";
import db from "../db";
import { systemEvents, SystemEvent } from "../schema";

export async function createSystemEvent(
  data: typeof systemEvents.$inferInsert
): Promise<SystemEvent> {
  const [row] = await db.insert(systemEvents).values(data).returning();
  return row;
}

export async function listSystemEvents(): Promise<SystemEvent[]> {
  return db.select().from(systemEvents);
}

export async function listSystemEventsByType(
  type: string
): Promise<SystemEvent[]> {
  return db.select().from(systemEvents).where(eq(systemEvents.eventType, type));
}

export async function initSystemEvents(): Promise<void> {
  const anyDb: any = db;
  const createTable = sql`
    CREATE TABLE IF NOT EXISTS system_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_type TEXT NOT NULL,
      source TEXT,
      agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
      instance_id INTEGER REFERENCES whatsapp_instances(id) ON DELETE SET NULL,
      data TEXT,
      created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
      updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
    )
  `;
  const createIndex = sql`
    CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events (event_type)
  `;
  if (typeof anyDb.run === "function") {
    await anyDb.run(createTable);
    await anyDb.run(createIndex);
  } else if (typeof anyDb.execute === "function") {
    await anyDb.execute(createTable);
    await anyDb.execute(createIndex);
  }
}
