import { eq } from "drizzle-orm";
import db from "../db";
import { messages, Message } from "../schema";

export async function createMessage(
  data: typeof messages.$inferInsert
): Promise<Message> {
  const [row] = await db.insert(messages).values(data).returning();
  return row;
}

export async function listMessagesByInstance(
  instanceId: number
): Promise<Message[]> {
  return db
    .select()
    .from(messages)
    .where(eq(messages.instanceId, instanceId));
}
