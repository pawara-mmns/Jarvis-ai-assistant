import { describe, expect, it } from "vitest";
import { parseBackendHealth } from "./backend-health";

describe("parseBackendHealth", () => {
  it("returns validated backend details", () => {
    const result = parseBackendHealth({
      status: "ok",
      service: "jarvis-agent",
      version: "0.5.1",
    });

    expect(result.version).toBe("0.5.1");
  });

  it("does not accept malformed boundary data", () => {
    expect(() => parseBackendHealth({ status: "ok" })).toThrow();
  });
});
