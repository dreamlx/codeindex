/** Entry point — cross-file CALLS into ./api. */

import { fetchUser } from "./api";

export async function bootstrap(id: number): Promise<unknown> {
  return fetchUser(id); // cross-file CALLS -> web.api.fetchUser
}
