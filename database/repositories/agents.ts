import { eq } from "drizzle-orm";
import db from "../db";
import { agents, Agent } from "../schema";

export async function createAgent(data: typeof agents.$inferInsert): Promise<Agent> {
  const [row] = await db.insert(agents).values(data).returning();
  return row;
}

export async function getAgentById(id: number): Promise<Agent | undefined> {
  const [row] = await db.select().from(agents).where(eq(agents.id, id));
  return row;
}

export async function listAgents(): Promise<Agent[]> {
  return db.select().from(agents);
}
