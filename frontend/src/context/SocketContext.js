import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from './AuthContext';

const SocketContext = createContext(null);

export const useSocket = () => useContext(SocketContext);

export const SocketProvider = ({ children }) => {
  const { token, API } = useAuth();
  const socketRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const processedIds = useRef(new Set()); // <-- INSERT THIS LINE
  useEffect(() => {
    if (!token || !API) return;

    // Derive the WebSocket base URL from API URL (strip /api suffix if present)
    const wsBase = API.replace(/\/api$/, '');

    const socket = io(wsBase, {
      path: '/api/ws/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
    });

    socket.on('connect', () => {
      console.log('[LiveHive] Connected:', socket.id);
      setConnected(true);
    });

    socket.on('disconnect', (reason) => {
      console.log('[LiveHive] Disconnected:', reason);
      setConnected(false);
    });

    socket.on('connect_error', (err) => {
      console.warn('[LiveHive] Connection error:', err.message);
    });

    socketRef.current = socket;
    // Block duplicate notifications
    socket.on('notification', (data) => {
      if (processedIds.current.has(data.id)) return;

      processedIds.current.add(data.id);
        
      // Safety: Keep the memory light
      if (processedIds.current.size > 100) {
        const firstValue = processedIds.current.values().next().value;
        processedIds.current.delete(firstValue);
      }

      // Trigger your visual alert here
      console.log('Unique notification received:', data);
      // If you have a toast function (like showToast), add it here!
    });
    return () => {
      socket.off('notification'); // Add this to stop the listener
      socket.disconnect();
      setConnected(false);
    };
  }, [token, API]);

  return (
    <SocketContext.Provider value={{ socket: socketRef.current, connected }}>
      {children}
    </SocketContext.Provider>
  );
};
