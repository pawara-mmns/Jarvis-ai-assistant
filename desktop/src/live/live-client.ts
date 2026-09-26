import {
  LIVE_MESSAGE_TYPES,
  liveConnectionInfoSchema,
  liveServerMessageSchema,
  type LiveClientMessage,
  type LiveServerMessage,
} from "@shared/schemas/live";
import { bytesToBase64 } from "../audio/pcm";

type LiveMessageListener = (message: LiveServerMessage) => void;

export class LiveBackendClient {
  private socket: WebSocket | null = null;
  private bridgeToken: string | null = null;
  private connectPromise: Promise<void> | null = null;
  private readonly listeners = new Set<LiveMessageListener>();

  subscribe(listener: LiveMessageListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  async connect(): Promise<void> {
    if (this.socket?.readyState === WebSocket.OPEN) {
      if (this.bridgeToken) {
        this.send({ type: LIVE_MESSAGE_TYPES.sessionStart, bridgeToken: this.bridgeToken });
      }
      return;
    }
    if (this.socket?.readyState === WebSocket.CONNECTING) {
      return this.connectPromise ?? Promise.resolve();
    }
    if (this.connectPromise) return this.connectPromise;

    this.connectPromise = this.connectInternal();
    try {
      await this.connectPromise;
    } finally {
      this.connectPromise = null;
    }
  }

  sendAudio(bytes: Uint8Array): void {
    this.send({
      type: LIVE_MESSAGE_TYPES.audioChunk,
      data: bytesToBase64(bytes),
      mimeType: "audio/pcm;rate=16000",
    });
  }

  endAudio(): void {
    this.send({ type: LIVE_MESSAGE_TYPES.audioEnd });
  }

  disconnect(): void {
    const socket = this.socket;
    this.socket = null;
    if (!socket) return;
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: LIVE_MESSAGE_TYPES.sessionStop } satisfies LiveClientMessage));
    }
    window.setTimeout(() => {
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close(1000, "AI session closed");
      }
    }, 250);
  }

  private async connectInternal(): Promise<void> {
    const connectionInfo = liveConnectionInfoSchema.parse(await window.jarvis.getLiveConnectionInfo());
    this.bridgeToken = connectionInfo.bridgeToken;
    await new Promise<void>((resolve, reject) => {
      const socket = new WebSocket(connectionInfo.webSocketUrl);
      this.socket = socket;
      socket.onopen = () => {
        this.send({ type: LIVE_MESSAGE_TYPES.sessionStart, bridgeToken: connectionInfo.bridgeToken });
        resolve();
      };
      socket.onmessage = (event) => this.handleMessage(event.data);
      socket.onerror = () => reject(new Error("Local AI connection failed."));
      socket.onclose = () => {
        if (this.socket === socket) this.socket = null;
        this.emit({ type: LIVE_MESSAGE_TYPES.sessionClosed });
      };
    });
  }

  private send(message: LiveClientMessage): void {
    if (this.socket?.readyState !== WebSocket.OPEN) return;
    this.socket.send(JSON.stringify(message));
  }

  private handleMessage(value: unknown): void {
    try {
      const parsed: unknown = typeof value === "string" ? JSON.parse(value) : value;
      this.emit(liveServerMessageSchema.parse(parsed));
    } catch (error) {
      console.warn("[live] ignored invalid backend message", error);
    }
  }

  private emit(message: LiveServerMessage): void {
    for (const listener of this.listeners) listener(message);
  }
}

export const liveBackendClient = new LiveBackendClient();
