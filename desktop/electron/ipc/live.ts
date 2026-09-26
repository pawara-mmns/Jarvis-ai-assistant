import { ipcMain } from "electron";
import { liveConnectionInfoSchema } from "../../../shared/schemas/live";
import { IPC_CHANNELS } from "../../../shared/ipc";
import type { BackendManager } from "../backend-manager";

export function registerLiveHandler(backendManager: BackendManager): void {
  ipcMain.handle(IPC_CHANNELS.liveConnectionInfo, () =>
    liveConnectionInfoSchema.parse({
      webSocketUrl: backendManager.liveWebSocketUrl,
      bridgeToken: backendManager.bridgeToken,
    }),
  );
}

export function unregisterLiveHandler(): void {
  ipcMain.removeHandler(IPC_CHANNELS.liveConnectionInfo);
}
