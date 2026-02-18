import { EventEmitter } from 'events';
import type { Logger } from './logger';

/**
 * User service for managing user operations.
 */

interface User {
  id: string;
  name: string;
  email: string;
}

enum UserRole {
  Admin = 'admin',
  Editor = 'editor',
  Viewer = 'viewer',
}

type UserMap = Map<string, User>;

class UserService extends EventEmitter implements Logger {
  private users: UserMap = new Map();
  private readonly maxUsers: number;

  constructor(maxUsers: number = 100) {
    super();
    this.maxUsers = maxUsers;
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async createUser(name: string, email: string): Promise<User> {
    const user: User = {
      id: crypto.randomUUID(),
      name,
      email,
    };
    this.users.set(user.id, user);
    this.emit('userCreated', user);
    return user;
  }

  static create(): UserService {
    return new UserService();
  }

  log(message: string): void {
    console.log(`[UserService] ${message}`);
  }
}

export default UserService;
export { User, UserRole, UserMap };
