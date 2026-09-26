import { create } from "zustand";
import type { BackendHealth } from "@shared/schemas/health";
import { getBackendHealth } from "../services/backend-health";

type ConnectionStatus = "connecting" | "connected" | "offline";

interface ConnectionStore {
  status: ConnectionStatus;
  health: BackendHealth | null;
  checkConnection(): Promise<void>;
}

export const useConnectionStore = create<ConnectionStore>((set) => ({
  status: "connecting",
  health: null,
  checkConnection: async () => {
    set({ status: "connecting", health: null });
    try {
      const health = await getBackendHealth();
      set({ status: "connected", health });
    } catch {
      set({ status: "offline", health: null });
    }
  },
}));
