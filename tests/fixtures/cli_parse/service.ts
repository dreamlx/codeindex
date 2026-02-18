import { Database } from './db';

interface UserDTO {
  id: string;
  name: string;
}

class UserService {
  constructor(private db: Database) {}

  async findById(id: string): Promise<UserDTO | null> {
    return this.db.query('SELECT * FROM users WHERE id = ?', [id]);
  }
}

export default UserService;
