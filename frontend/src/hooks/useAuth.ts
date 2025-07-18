import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from './redux';
import { login, logout, fetchCurrentUser } from '../store/slices/authSlice';
import authService from '../services/auth.service';
import type { LoginRequest } from '../types/auth.types';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading, error } = useAppSelector(state => state.auth);

  const handleLogin = useCallback(async (credentials: LoginRequest) => {
    try {
      await dispatch(login(credentials)).unwrap();
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    }
  }, [dispatch, navigate]);

  const handleLogout = useCallback(async () => {
    try {
      await dispatch(logout()).unwrap();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      // Even if logout fails, navigate to login
      navigate('/login');
    }
  }, [dispatch, navigate]);

  const checkAuth = useCallback(async () => {
    if (authService.isAuthenticated()) {
      try {
        await dispatch(fetchCurrentUser()).unwrap();
      } catch (error) {
        console.error('Failed to fetch user:', error);
      }
    }
  }, [dispatch]);

  const hasRole = useCallback((role: string) => {
    return authService.hasRole(user, role);
  }, [user]);

  const hasPermission = useCallback((permission: string) => {
    return authService.hasPermission(user, permission);
  }, [user]);

  const hasAnyRole = useCallback((roles: string[]) => {
    return authService.hasAnyRole(user, roles);
  }, [user]);

  const hasAnyPermission = useCallback((permissions: string[]) => {
    return authService.hasAnyPermission(user, permissions);
  }, [user]);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    logout: handleLogout,
    checkAuth,
    hasRole,
    hasPermission,
    hasAnyRole,
    hasAnyPermission,
  };
};