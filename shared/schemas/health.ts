import { z } from "zod";

export const backendHealthSchema = z.object({
  status: z.literal("ok"),
  service: z.literal("jarvis-agent"),
  version: z.string().regex(/^\d+\.\d+\.\d+$/),
});

export type BackendHealth = z.infer<typeof backendHealthSchema>;
