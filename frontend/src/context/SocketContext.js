import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';

const SocketContext = createContext(null);

export const useSocket = () => useContext(SocketContext);

export const SocketProvider = ({ children }) => {
  const { token, API } = useAuth();
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const processedIds = useRef(new Set());
  const reconnectCount = useRef(0);

  useEffect(() => {
    if (!token || !API) return;

    // Clean up any existing socket before creating new one
    if (socketRef.current) {
      socketRef.current.removeAllListeners();
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    const wsBase = API.replace(/\/api$/, '');

    const socket = io(wsBase, {
      path: '/api/ws/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
      forceNew: true,
    });

    socket.on('connect', () => {
      console.log('[LiveHive] Connected:', socket.id);
      setConnected(true);
      reconnectCount.current = 0;
    });

    socket.on('disconnect', (reason) => {
      console.log('[LiveHive] Disconnected:', reason);
      setConnected(false);
    });

    socket.on('connect_error', (err) => {
      reconnectCount.current += 1;
      if (reconnectCount.current <= 3) {
        console.warn('[LiveHive] Connection error:', err.message);
      }
    });

    // Deduplicated notification handler
    socket.on('notification', (data) => {
      if (!data?.id) return;
      if (processedIds.current.has(data.id)) return;
      processedIds.current.add(data.id);
      // Cap memory usage
      if (processedIds.current.size > 200) {
        const iter = processedIds.current.values();
        processedIds.current.delete(iter.next().value);
      }
    });

    socketRef.current = socket;

    return () => {
      socket.removeAllListeners();
      socket.disconnect();
      socketRef.current = null;
      setConnected(false);
    };
  }, [token, API]);

  return (
    <SocketContext.Provider value={{ socket: socketRef.current, connected }}>
      {children}
    </SocketContext.Provider>
  );
};
