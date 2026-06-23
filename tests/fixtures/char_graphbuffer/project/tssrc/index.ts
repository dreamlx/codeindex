/** Entry point for the demo TS module. */

import { fetchUser } from "./api";

export interface Account {
  id: number;
  name: string;
}

export class AccountStore {
  private accounts: Map<number, Account> = new Map();

  add(account: Account): void {
    this.accounts.set(account.id, account);
  }

  get(id: number): Account | undefined {
    return this.accounts.get(id);
  }
}

export async function bootstrap(id: number): Promise<Account | undefined> {
  const store = new AccountStore();
  const user = await fetchUser(id);
  if (user) {
    store.add(user);
  }
  return store.get(id);
}
