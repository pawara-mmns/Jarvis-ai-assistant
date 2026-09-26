import { backendHealthSchema, type BackendHealth } from "@shared/schemas/health";

export function parseBackendHealth(value: unknown): BackendHealth {
  return backendHealthSchema.parse(value);
}

export async function getBackendHealth(): Promise<BackendHealth> {
  const response = await window.jarvis.getBackendHealth();
  return parseBackendHealth(response);
}
