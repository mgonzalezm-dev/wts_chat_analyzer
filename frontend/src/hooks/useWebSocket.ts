import { useEffect, useCallback } from 'react';
import { useSelector } from 'react-redux';
import type { RootState } from '../store';
import { websocketService } from '../services/websocket.service';

export interface UseWebSocketOptions {
  onMessage?: (type: string, data: any) => void;
  autoConnect?: boolean;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const { onMessage, autoConnect = true } = options;
  const user = useSelector((state: RootState) => state.auth.user);
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated);
  const token = user?.id; // Use user ID as token for now

  useEffect(() => {
    if (autoConnect && isAuthenticated && token) {
      websocketService.connect(token);
    }

    return () => {
      if (autoConnect) {
        websocketService.disconnect();
      }
    };
  }, [isAuthenticated, token, autoConnect]);

  useEffect(() => {
    if (onMessage) {
      const messageTypes = [
        'conversation_update',
        'export_complete',
        'analytics_ready',
        'error',
        'notification'
      ];

      const handlers = messageTypes.map(type => {
        const handler = (data: any) => onMessage(type, data);
        websocketService.on(type, handler);
        return { type, handler };
      });

      return () => {
        handlers.forEach(({ type, handler }) => {
          websocketService.off(type, handler);
        });
      };
    }
  }, [onMessage]);

  const send = useCallback((data: any) => {
    websocketService.send(data);
  }, []);

  const subscribe = useCallback((type: string, handler: (data: any) => void) => {
    websocketService.on(type, handler);
    return () => websocketService.off(type, handler);
  }, []);

  return {
    send,
    subscribe,
    isConnected: websocketService.isConnected()
  };
};