import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { app, BrowserWindow } from "electron";
import { BackendManager } from "./backend-manager";
import { registerHealthHandler, unregisterHealthHandler } from "./ipc/health";

const currentDirectory = fileURLToPath(new URL(".", import.meta.url));
let backendManager: BackendManager | null = null;
let shutdownStarted = false;

function createWindow(): void {
  const window = new BrowserWindow({
    width: 1180,
    height: 760,
    minWidth: 820,
    minHeight: 600,
    show: false,
    backgroundColor: "#080b10",
    webPreferences: {
      preload: join(currentDirectory, "../preload/preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  window.once("ready-to-show", () => window.show());

  const rendererUrl = process.env.ELECTRON_RENDERER_URL;
  if (rendererUrl) {
    void window.loadURL(rendererUrl);
  } else {
    void window.loadFile(join(currentDirectory, "../renderer/index.html"));
  }
}

app.whenReady().then(async () => {
  backendManager = new BackendManager(app.getAppPath());
  registerHealthHandler(backendManager);

  try {
    await backendManager.start();
  } catch (error) {
    console.error("[desktop] agent startup failed", error);
  }

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", (event) => {
  if (shutdownStarted || !backendManager) return;
  event.preventDefault();
  shutdownStarted = true;
  unregisterHealthHandler();
  void backendManager.stop().finally(() => app.quit());
});
