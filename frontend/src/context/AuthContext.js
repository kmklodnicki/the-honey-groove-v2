import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import safeStorage from '../utils/safeStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
const API = `${BACKEND_URL}/api`;

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
  return {
    id: payload.user_id || payload.sub || payload.id,
    email: payload.email || '',
    username: payload.username || '',
    _fromToken: true,
    _hydrated: !!(payload.username), // true if JWT has full data
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
    // Request persistent storage for PWA standalone mode
    if (navigator.storage && navigator.storage.persist) {
      navigator.storage.persist().catch(() => {});
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchUserBackground = async () => {
    try {
      console.log('AUTH: background user fetch');
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 15000,
      });
      setUser(response.data);
      console.log('AUTH: user data refreshed');
    } catch (error) {
      if (error.response && (error.response.status === 401 || error.response.status === 403)) {
        console.error('AUTH: token rejected, logging out');
        logout();
      } else if (error.response && error.response.status === 405) {
        // Fallback: GET /auth/me not deployed yet — fetch via public profile endpoint
        console.warn('AUTH: GET /auth/me not available (405), trying fallback');
        try {
          const currentUser = user;
          if (currentUser?.username) {
            const fallback = await axios.get(`${API}/users/${currentUser.username}`, {
              headers: { Authorization: `Bearer ${token}` },
              timeout: 10000,
            });
            if (fallback.data) {
              setUser(prev => ({ ...prev, ...fallback.data }));
              console.log('AUTH: user data refreshed via fallback');
            }
          }
        } catch (fbErr) {
          console.warn('AUTH: fallback also failed', fbErr.message);
        }
      } else {
        console.warn('AUTH: background fetch failed (network), keeping session', error.message);
      }
    }
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;
    safeStorage.setItem('honeygroove_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, username) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, username });
    const { access_token, user: userData } = response.data;
    safeStorage.setItem('honeygroove_token', access_token);
    setToken(access_token);
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
