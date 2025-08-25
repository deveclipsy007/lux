import db from "../db";

/**
 * Runs the provided callback within a database transaction.
 */
export async function withTransaction<T>(
  fn: (tx: typeof db) => Promise<T>
): Promise<T> {
  return db.transaction(fn);
}
