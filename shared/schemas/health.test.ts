import { describe, expect, it } from "vitest";
import { backendHealthSchema } from "./health";

describe("backendHealthSchema", () => {
  it("accepts the Phase 0 health contract", () => {
    expect(
      backendHealthSchema.parse({
        status: "ok",
        service: "jarvis-agent",
        version: "0.2.0",
      }),
    ).toEqual({ status: "ok", service: "jarvis-agent", version: "0.2.0" });
  });

  it("rejects an unexpected service", () => {
    expect(() =>
      backendHealthSchema.parse({
        status: "ok",
        service: "unknown",
        version: "0.2.0",
      }),
    ).toThrow();
  });
});
