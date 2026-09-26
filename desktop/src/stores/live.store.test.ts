import { beforeEach, describe, expect, it } from "vitest";
import { liveUiInitialState, useLiveStore } from "./live.store";

describe("AI connection store", () => {
  beforeEach(() => useLiveStore.setState(liveUiInitialState));

  it("tracks connection, streaming, and playback independently", () => {
    const store = useLiveStore.getState();
    store.setConnectionState("ready");
    store.setStreaming(true);
    store.setPlayback("playing", 0.7, new Array(24).fill(0.5));
    expect(useLiveStore.getState()).toMatchObject({
      connectionState: "ready",
      streaming: true,
      outputPlaybackState: "playing",
      outputLevel: 0.7,
    });
  });
});

