import type { BackendHealth } from "@shared/schemas/health";

export interface JarvisApi {
  getBackendHealth(): Promise<BackendHealth>;
}

declare global {
  interface Window {
    jarvis: JarvisApi;
  }
}

export {};
