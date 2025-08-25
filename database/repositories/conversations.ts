import { eq } from "drizzle-orm";
import db from "../db";
import { conversations, Conversation } from "../schema";

export async function createConversation(
  data: typeof conversations.$inferInsert
): Promise<Conversation> {
  const [row] = await db.insert(conversations).values(data).returning();
  return row;
}

export async function getConversationByChatId(
  chatId: string
): Promise<Conversation | undefined> {
  const [row] = await db
    .select()
    .from(conversations)
    .where(eq(conversations.chatId, chatId));
  return row;
}
