import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AssistantStatus } from "./AssistantStatus";

describe("AssistantStatus", () => {
  it("renders the shared state label and execution context", () => {
    const markup = renderToStaticMarkup(
      createElement(AssistantStatus, {
        state: "executing",
        executionLabel: "Launching development environment...",
      }),
    );

    expect(markup).toContain("Executing...");
    expect(markup).toContain("Launching development environment...");
    expect(markup).toContain('aria-live="polite"');
  });
});
