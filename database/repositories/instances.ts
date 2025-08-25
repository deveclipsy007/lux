import { eq } from "drizzle-orm";
import db from "../db";
import { whatsappInstances, WhatsappInstance } from "../schema";

export async function createInstance(
  data: typeof whatsappInstances.$inferInsert
): Promise<WhatsappInstance> {
  const [row] = await db.insert(whatsappInstances).values(data).returning();
  return row;
}

export async function getInstanceById(
  id: number
): Promise<WhatsappInstance | undefined> {
  const [row] = await db
    .select()
    .from(whatsappInstances)
    .where(eq(whatsappInstances.id, id));
  return row;
}

export async function listInstances(): Promise<WhatsappInstance[]> {
  return db.select().from(whatsappInstances);
}

export async function updateInstance(
  id: number,
  data: Partial<typeof whatsappInstances.$inferInsert>
): Promise<WhatsappInstance | undefined> {
  const [row] = await db
    .update(whatsappInstances)
    .set(data)
    .where(eq(whatsappInstances.id, id))
    .returning();
  return row;
}
