import { ipcMain } from "electron";
import { IPC_CHANNELS } from "../../../shared/ipc";
import type { BackendManager } from "../backend-manager";

export function registerHealthHandler(backendManager: BackendManager): void {
  ipcMain.handle(IPC_CHANNELS.backendHealth, async () => backendManager.getHealth());
}

export function unregisterHealthHandler(): void {
  ipcMain.removeHandler(IPC_CHANNELS.backendHealth);
}
