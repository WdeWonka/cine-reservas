export type Role = 'admin' | 'taquillero';

export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserOut {
  user_id: number;
  username: string;
  role: Role;
  is_active: boolean;
}
