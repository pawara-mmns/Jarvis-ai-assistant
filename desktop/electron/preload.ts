import { contextBridge, ipcRenderer } from "electron";
import type { BackendHealth } from "../../shared/schemas/health";
import { IPC_CHANNELS } from "../../shared/ipc";

const jarvisApi = {
  async getBackendHealth(): Promise<BackendHealth> {
    const result: unknown = await ipcRenderer.invoke(IPC_CHANNELS.backendHealth);
    return result as BackendHealth;
  },
};

contextBridge.exposeInMainWorld("jarvis", Object.freeze(jarvisApi));
