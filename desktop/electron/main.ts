import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { app, BrowserWindow, session } from "electron";
import { BackendManager } from "./backend-manager";
import { registerHealthHandler, unregisterHealthHandler } from "./ipc/health";
import { registerLiveHandler, unregisterLiveHandler } from "./ipc/live";

const currentDirectory = fileURLToPath(new URL(".", import.meta.url));
let backendManager: BackendManager | null = null;
let shutdownStarted = false;
const trustedRendererIds = new Set<number>();

function configureMediaPermissions(): void {
  session.defaultSession.setPermissionRequestHandler(
    (webContents, permission, callback, details) => {
      const mediaTypes = "mediaTypes" in details ? (details.mediaTypes ?? []) : [];
      const isAudioOnlyRequest =
        permission === "media" &&
        mediaTypes.length > 0 &&
        mediaTypes.every((mediaType) => mediaType === "audio");
      callback(trustedRendererIds.has(webContents.id) && isAudioOnlyRequest);
    },
  );

  session.defaultSession.setPermissionCheckHandler((webContents, permission, _origin, details) => {
    return Boolean(
      webContents &&
        trustedRendererIds.has(webContents.id) &&
        permission === "media" &&
        details.mediaType === "audio",
    );
  });
}

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
  const rendererId = window.webContents.id;
  trustedRendererIds.add(rendererId);
  window.webContents.once("destroyed", () => trustedRendererIds.delete(rendererId));

  window.once("ready-to-show", () => window.show());

  const rendererUrl = process.env.ELECTRON_RENDERER_URL;
  if (rendererUrl) {
    void window.loadURL(rendererUrl);
  } else {
    void window.loadFile(join(currentDirectory, "../renderer/index.html"));
  }
}

app.whenReady().then(async () => {
  configureMediaPermissions();
  backendManager = new BackendManager(app.getAppPath(), app.getVersion());
  registerHealthHandler(backendManager);
  registerLiveHandler(backendManager);

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
  unregisterLiveHandler();
  void backendManager.stop().finally(() => app.quit());
});
