import { eq } from "drizzle-orm";
import db from "../db";
import { systemEvents, SystemEvent } from "../schema";

export async function logEvent(
  data: typeof systemEvents.$inferInsert
): Promise<SystemEvent> {
  const [row] = await db.insert(systemEvents).values(data).returning();
  return row;
}

export async function listEventsByType(
  type: string
): Promise<SystemEvent[]> {
  return db.select().from(systemEvents).where(eq(systemEvents.eventType, type));
}
