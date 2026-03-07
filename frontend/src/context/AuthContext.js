import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import safeStorage from '../utils/safeStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

// Decode JWT payload client-side (no network call needed)
function decodeTokenPayload(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(atob(base64));
    // Check if token is expired
    if (payload.exp && payload.exp * 1000 < Date.now()) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

// Initialize user from token without any network call
function initUserFromToken(token) {
  if (!token) return null;
  const payload = decodeTokenPayload(token);
  if (!payload) return null;
  // Return a minimal user object from JWT claims
  // The real user data will be fetched in the background
  return {
    id: payload.user_id || payload.sub || payload.id,
    email: payload.email || '',
    username: payload.username || '',
    _fromToken: true, // flag: this is partial data from JWT
  };
}

export const AuthProvider = ({ children }) => {
  const storedToken = safeStorage.getItem('honeygroove_token');
  // CRITICAL: loading starts as FALSE. The page renders IMMEDIATELY.
  // If a token exists, we decode it client-side for instant user hydration.
  const [token, setToken] = useState(storedToken);
  const [user, setUser] = useState(() => initUserFromToken(storedToken));
  const [loading] = useState(false); // NEVER true. No loading gates.

  // Set up axios interceptor for auth header
  useEffect(() => {
    const interceptor = axios.interceptors.request.use((config) => {
      const t = safeStorage.getItem('honeygroove_token');
      if (t) config.headers.Authorization = `Bearer ${t}`;
      return config;
    });
    return () => axios.interceptors.request.eject(interceptor);
  }, []);

  // Background fetch: refresh user data silently after page renders
  useEffect(() => {
    if (token) {
      fetchUserBackground();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchUserBackground = async () => {
    try {
      console.log('AUTH: background user fetch');
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 8000,
      });
      if (response.data.email_verified === false) {
        logout();
        return;
      }
      // Merge full user data (replaces the partial JWT-decoded user)
      setUser(response.data);
      console.log('AUTH: user data refreshed');
    } catch (error) {
      console.error('AUTH: background fetch failed', error);
      // Token is invalid or expired — clear session
      logout();
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;
    safeStorage.setItem('honeygroove_token', access_token);
    setToken(access_token);
    if (userData.email_verified === false) {
      return userData;
    }
    setUser(userData);
    return userData;
  };

  const register = async (email, password, username) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, username });
    const { access_token, user: userData } = response.data;
    safeStorage.setItem('honeygroove_token', access_token);
    setToken(access_token);
    if (userData.email_verified === false) {
      return userData;
    }
    setUser(userData);
    return userData;
  };

  const logout = () => {
    safeStorage.removeItem('honeygroove_token');
    setToken(null);
    setUser(null);
  };

  const updateUser = (data) => {
    if (typeof data === 'function') setUser(prev => data(prev));
    else setUser(prev => ({ ...prev, ...data }));
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, updateUser, setToken, setUser, API }}>
      {children}
    </AuthContext.Provider>
  );
};

export { API };
