import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import safeStorage from '../utils/safeStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => safeStorage.getItem('honeygroove_token'));
  const [loading, setLoading] = useState(true);

  // Set up axios interceptor for auth header
  useEffect(() => {
    const interceptor = axios.interceptors.request.use((config) => {
      const storedToken = safeStorage.getItem('honeygroove_token');
      if (storedToken) {
        config.headers.Authorization = `Bearer ${storedToken}`;
      }
      return config;
    });

    return () => {
      axios.interceptors.request.eject(interceptor);
    };
  }, []);

  useEffect(() => {
    console.log('AUTH INIT, token exists:', !!token);
    if (token) {
      fetchUser();
    } else {
      console.log('AUTH RESOLVED, loading: false (no token)');
      setLoading(false);
    }
    // Hard safety timeout: force loading=false after 5 seconds no matter what.
    const safetyTimer = setTimeout(() => {
      console.log('AUTH SAFETY TIMEOUT, forcing loading: false');
      setLoading(false);
    }, 5000);
    return () => clearTimeout(safetyTimer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchUser = async () => {
    try {
      console.log('AUTH fetchUser START');
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000
      });
      if (response.data.email_verified === false) {
        logout();
        return;
      }
      setUser(response.data);
      console.log('AUTH RESOLVED, loading: false (user loaded)');
    } catch (error) {
      console.error('Auth error:', error);
      logout();
    } finally {
      setLoading(false);
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
