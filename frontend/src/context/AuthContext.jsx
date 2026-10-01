import { createContext, useContext, useState } from 'react';
import * as api from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [email, setEmail] = useState(() => localStorage.getItem('email') || null);

  const login = async (emailInput, password) => {
    const data = await api.login(emailInput, password);
    api.setToken(data.access_token);
    localStorage.setItem('email', emailInput);
    setEmail(emailInput);
  };

  const register = async (emailInput, password) => {
    await api.register(emailInput, password);
    await login(emailInput, password);
  };

  const logout = () => {
    api.clearToken();
    localStorage.removeItem('email');
    setEmail(null);
  };

  return (
    <AuthContext.Provider value={{ email, isAuthenticated: !!email, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
