import { describe, expect, it } from "vitest";
import { LIVE_MESSAGE_TYPES, liveClientMessageSchema, liveServerMessageSchema } from "./live";

describe("live message schemas", () => {
  it("accepts the narrow PCM input contract", () => {
    expect(
      liveClientMessageSchema.parse({
        type: LIVE_MESSAGE_TYPES.audioChunk,
        data: "AQI=",
        mimeType: "audio/pcm;rate=16000",
      }),
    ).toMatchObject({ type: "audio.chunk", mimeType: "audio/pcm;rate=16000" });
  });

  it("rejects unknown commands and malformed output", () => {
    expect(() => liveClientMessageSchema.parse({ type: "desktop.execute" })).toThrow();
    expect(() =>
      liveServerMessageSchema.parse({ type: "audio.output", data: "", mimeType: "audio/mpeg" }),
    ).toThrow();
  });
});

