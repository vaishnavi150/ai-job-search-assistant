import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import * as api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // 'checking' until a stored token has been verified with the server.
  const [status, setStatus] = useState(() => (api.getToken() ? 'checking' : 'anonymous'));
  const [sessionExpired, setSessionExpired] = useState(false);

  const clearSessionExpired = useCallback(() => setSessionExpired(false), []);

  const logout = useCallback(() => {
    api.clearToken();
    setUser(null);
    setStatus('anonymous');
  }, []);

  useEffect(() => {
    if (!api.getToken()) return;
    let cancelled = false;
    api.getMe()
      .then((me) => {
        if (!cancelled) {
          setUser(me);
          setStatus('authenticated');
        }
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401) {
          logout();
        } else {
          // Server unreachable: keep the token, let pages show their own errors.
          setStatus('authenticated');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [logout]);

  useEffect(
    () =>
      api.onApiEvent('api:unauthorized', () => {
        if (api.getToken()) setSessionExpired(true);
        logout();
      }),
    [logout],
  );

  const startSession = async (token) => {
    api.setToken(token);
    const me = await api.getMe();
    setUser(me);
    setStatus('authenticated');
    setSessionExpired(false);
  };

  const login = async (email, password) => {
    const data = await api.login(email.trim(), password);
    await startSession(data.access_token);
  };

  const register = async (email, password, confirmPassword) => {
    await api.register(email.trim(), password, confirmPassword);
    await login(email, password);
  };

  const value = {
    user,
    email: user?.email ?? null,
    status,
    isAuthenticated: status === 'authenticated',
    sessionExpired,
    clearSessionExpired,
    login,
    register,
    logout,
    startSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
