import { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { setUnauthorizedHandler } from '../services/api.js';
import { authService } from '../services/authService.js';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('checking');

  const clearSession = useCallback(() => {
    setUser(null);
    setStatus('unauthenticated');
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(clearSession);
    return () => setUnauthorizedHandler(null);
  }, [clearSession]);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      try {
        const currentUser = await authService.getCurrentUser();
        if (!active) return;
        setUser(currentUser);
        setStatus('authenticated');
      } catch (error) {
        if (!active) return;
        setUser(null);
        setStatus('unauthenticated');
      }
    }

    restoreSession();

    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    const authenticatedUser = await authService.login(email, password);
    setUser(authenticatedUser);
    setStatus('authenticated');
    return authenticatedUser;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const value = useMemo(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated',
      isChecking: status === 'checking',
      login,
      logout,
      clearSession,
    }),
    [clearSession, login, logout, status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
