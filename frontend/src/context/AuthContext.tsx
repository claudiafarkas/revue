import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react';
import { getStoredToken, getStoredUser, setAuth, clearAuth, type AuthUser } from '../lib/auth';
import { getApiBaseUrl } from '../utils/api';

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signOutUser: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore auth on mount
  useEffect(() => {
    const storedUser = getStoredUser();
    const storedToken = getStoredToken();
    
    if (storedUser && storedToken) {
      setUser(storedUser);
    }
    setLoading(false);
  }, []);

  const signUpWithEmail = useCallback(async (email: string, password: string) => {
    const response = await fetch(`${getApiBaseUrl()}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    const data = await response.json();
    const authUser: AuthUser = {
      user_id: data.user_id,
      email: data.email,
    };
    setAuth(data.access_token, authUser);
    setUser(authUser);
  }, []);

  const signInWithEmail = useCallback(async (email: string, password: string) => {
    const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    const authUser: AuthUser = {
      user_id: data.user_id,
      email: data.email,
    };
    setAuth(data.access_token, authUser);
    setUser(authUser);
  }, []);

  const signOutUser = useCallback(async () => {
    clearAuth();
    setUser(null);
  }, []);

  const getIdToken = useCallback(async () => {
    return getStoredToken();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      signUpWithEmail,
      signInWithEmail,
      signOutUser,
      getIdToken,
    }),
    [user, loading, signUpWithEmail, signInWithEmail, signOutUser, getIdToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
