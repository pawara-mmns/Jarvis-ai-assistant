import type { BackendHealth } from "@shared/schemas/health";
import type { LiveConnectionInfo } from "@shared/schemas/live";

export interface JarvisApi {
  getBackendHealth(): Promise<BackendHealth>;
  getLiveConnectionInfo(): Promise<LiveConnectionInfo>;
}

declare global {
  interface Window {
    jarvis: JarvisApi;
  }
}

export {};
