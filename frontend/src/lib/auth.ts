/**
 * Local authentication utilities for JWT-based auth.
 * No external cloud dependencies.
 */

const JWT_TOKEN_KEY = 'revue_auth_token';
const JWT_USER_KEY = 'revue_auth_user';

export interface AuthUser {
  user_id: string;
  email: string;
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(JWT_TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  const userJson = localStorage.getItem(JWT_USER_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson);
  } catch {
    return null;
  }
}

export function setAuth(token: string, user: AuthUser): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(JWT_TOKEN_KEY, token);
  localStorage.setItem(JWT_USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(JWT_TOKEN_KEY);
  localStorage.removeItem(JWT_USER_KEY);
}
