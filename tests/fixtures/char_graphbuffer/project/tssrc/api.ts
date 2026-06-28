/** Tiny typed data-access layer (exercises generics). */

import type { Account } from "./index";

interface Row {
  id: number;
  name: string;
}

export async function queryRaw<T>(sql: string): Promise<T[]> {
  // Pretend to run a query; generic return type exercises the parser.
  return [] as T[];
}

export async function fetchUser(id: number): Promise<Account | undefined> {
  const rows = await queryRaw<Row>(`SELECT * FROM users WHERE id = ${id}`);
  const row = rows[0];
  return row ? { id: row.id, name: row.name } : undefined;
}
