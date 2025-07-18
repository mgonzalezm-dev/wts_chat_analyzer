import { api, setTokens, clearTokens } from './api';
import type { LoginRequest, LoginResponse, User } from '../types/auth.types';

class AuthService {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login', credentials);
    const data = response.data.data!;
    
    // Store tokens
    setTokens(data.access_token, data.refresh_token);
    
    return data;
  }

  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API call failed:', error);
    } finally {
      clearTokens();
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data.data!;
  }

  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    const data = response.data.data!;
    
    // Update tokens
    setTokens(data.access_token, data.refresh_token);
    
    return data;
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  async requestPasswordReset(email: string): Promise<void> {
    await api.post('/auth/request-password-reset', { email });
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  }

  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    if (!token) return false;

    try {
      // Decode JWT to check expiration
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expirationTime = payload.exp * 1000; // Convert to milliseconds
      return Date.now() < expirationTime;
    } catch (error) {
      return false;
    }
  }

  hasRole(user: User | null, role: string): boolean {
    return user?.roles?.includes(role) || false;
  }

  hasPermission(user: User | null, permission: string): boolean {
    return user?.permissions?.includes(permission) || false;
  }

  hasAnyRole(user: User | null, roles: string[]): boolean {
    return roles.some(role => this.hasRole(user, role));
  }

  hasAnyPermission(user: User | null, permissions: string[]): boolean {
    return permissions.some(permission => this.hasPermission(user, permission));
  }
}

export default new AuthService();