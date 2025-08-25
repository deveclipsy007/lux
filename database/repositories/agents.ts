import { eq, sql } from "drizzle-orm";
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

export async function initAgents(): Promise<void> {
  const query = sql`
    CREATE TABLE IF NOT EXISTS agents (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      specialization TEXT,
      instructions TEXT,
      status TEXT NOT NULL DEFAULT 'inactive',
      created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
      updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
    )
  `;
  const anyDb: any = db;
  if (typeof anyDb.run === "function") {
    await anyDb.run(query);
  } else if (typeof anyDb.execute === "function") {
    await anyDb.execute(query);
  }
}

export async function updateAgent(
  id: number,
  data: Partial<typeof agents.$inferInsert>
): Promise<Agent | undefined> {
  const [row] = await db
    .update(agents)
    .set(data)
    .where(eq(agents.id, id))
    .returning();
  return row;
}

export async function deleteAgent(id: number): Promise<boolean> {
  const rows = await db.delete(agents).where(eq(agents.id, id)).returning();
  return rows.length > 0;
}
