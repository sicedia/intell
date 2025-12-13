import { env } from "./env";

export interface WSConfig {
  onMessage?: (data: unknown) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
  onOpen?: () => void;
}

export class WSClient {
  private ws: WebSocket | null = null;
  private url: string;
  private config: WSConfig;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  constructor(endpoint: string, config: WSConfig = {}) {
    const baseUrl = env.NEXT_PUBLIC_WS_BASE_URL.replace(/\/$/, "");
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    this.url = `${baseUrl}${cleanEndpoint}`;
    this.config = config;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.config.onOpen?.();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.config.onMessage?.(data);
        } catch {
          this.config.onMessage?.(event.data);
        }
      };

      this.ws.onerror = (error) => {
        this.config.onError?.(error);
      };

      this.ws.onclose = () => {
        this.config.onClose?.();
        this.attemptReconnect();
      };
    } catch (error) {
      console.error("WebSocket connection error:", error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(typeof data === "string" ? data : JSON.stringify(data));
    } else {
      console.warn("WebSocket is not connected");
    }
  }

  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}
