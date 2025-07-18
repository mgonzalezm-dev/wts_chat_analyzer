import { store } from '../store';
import { addNotification } from '../store/slices/uiSlice';

export interface WebSocketMessage {
  type: 'conversation_update' | 'export_complete' | 'analytics_ready' | 'error' | 'notification';
  data: any;
  timestamp: string;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;
  private maxReconnectAttempts: number = 5;
  private reconnectAttempts: number = 0;
  private heartbeatInterval: number | null = null;
  private messageHandlers: Map<string, Set<(data: any) => void>> = new Map();

  connect(token: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = this.getWebSocketUrl();
    this.ws = new WebSocket(`${wsUrl}?token=${token}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      
      // Send initial authentication
      this.send({
        type: 'auth',
        data: { token }
      });
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.stopHeartbeat();
      this.attemptReconnect(token);
    };
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  on(type: string, handler: (data: any) => void): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);
  }

  off(type: string, handler: (data: any) => void): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private handleMessage(message: WebSocketMessage): void {
    // Dispatch to Redux store based on message type
    switch (message.type) {
      case 'conversation_update':
        // TODO: Add conversation update action to conversationSlice
        store.dispatch(addNotification({
          type: 'info',
          message: `Conversation ${message.data.status}: ${message.data.progress}%`
        }));
        break;

      case 'export_complete':
        store.dispatch(addNotification({
          type: 'success',
          message: `Export completed: ${message.data.filename}`
        }));
        break;

      case 'analytics_ready':
        store.dispatch(addNotification({
          type: 'info',
          message: 'Analytics are ready for viewing'
        }));
        break;

      case 'error':
        store.dispatch(addNotification({
          type: 'error',
          message: message.data.message || 'An error occurred'
        }));
        break;

      case 'notification':
        store.dispatch(addNotification({
          type: message.data.level || 'info',
          message: message.data.message
        }));
        break;
    }

    // Call registered handlers
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message.data));
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' });
      }
    }, 30000); // 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      window.clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private attemptReconnect(token: string): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      store.dispatch(addNotification({
        type: 'error',
        message: 'Connection lost. Please refresh the page.'
      }));
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    setTimeout(() => {
      this.connect(token);
    }, this.reconnectInterval);
  }

  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    // In development, use the backend port directly
    if (import.meta.env.DEV) {
      return `${protocol}//localhost:8000/ws`;
    }
    
    // In production, use the same host with /ws path
    return `${protocol}//${host}/ws`;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();