import { contextBridge, ipcRenderer } from "electron";
import type { BackendHealth } from "../../shared/schemas/health";
import type { LiveConnectionInfo } from "../../shared/schemas/live";
import { IPC_CHANNELS } from "../../shared/ipc";

const jarvisApi = {
  async getBackendHealth(): Promise<BackendHealth> {
    const result: unknown = await ipcRenderer.invoke(IPC_CHANNELS.backendHealth);
    return result as BackendHealth;
  },
  async getLiveConnectionInfo(): Promise<LiveConnectionInfo> {
    const result: unknown = await ipcRenderer.invoke(IPC_CHANNELS.liveConnectionInfo);
    return result as LiveConnectionInfo;
  },
};

contextBridge.exposeInMainWorld("jarvis", Object.freeze(jarvisApi));
