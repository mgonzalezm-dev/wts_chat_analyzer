export interface User {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions?: string[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface TokenPayload {
  sub: string;
  email: string;
  roles: string[];
  exp: number;
  iat: number;
}