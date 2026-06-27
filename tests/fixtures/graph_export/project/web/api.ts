/** Tiny typed data-access layer (generics + intra-file CALLS). */

export async function queryRaw<T>(sql: string): Promise<T[]> {
  return [] as T[];
}

export async function fetchUser(id: number): Promise<unknown> {
  return queryRaw<unknown>(`SELECT * FROM users WHERE id = ${id}`); // intra-file CALLS
}
