import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('honeygroove_token'));
  const [loading, setLoading] = useState(true);

  // Set up axios interceptor for auth header
  useEffect(() => {
    const interceptor = axios.interceptors.request.use((config) => {
      const storedToken = localStorage.getItem('honeygroove_token');
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
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
    // Hard safety timeout: force loading=false after 3 seconds no matter what.
    // Prevents Safari from hanging indefinitely on a blank screen.
    const safetyTimer = setTimeout(() => {
      setLoading(false);
    }, 3000);
    return () => clearTimeout(safetyTimer);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000
      });
      if (response.data.email_verified === false) {
        logout();
        return;
      }
      setUser(response.data);
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
    localStorage.setItem('honeygroove_token', access_token);
    setToken(access_token);
    // Don't set user if email not verified — keep them on login page
    if (userData.email_verified === false) {
      return userData;
    }
    setUser(userData);
    return userData;
  };

  const register = async (email, password, username) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, username });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('honeygroove_token', access_token);
    setToken(access_token);
    if (userData.email_verified === false) {
      return userData;
    }
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('honeygroove_token');
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
