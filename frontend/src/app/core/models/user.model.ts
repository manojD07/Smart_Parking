export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_admin: boolean;
  is_active: boolean;
  total_spent: number;
  created_at: string;
  updated_at: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRegistration {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user?: User;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}
