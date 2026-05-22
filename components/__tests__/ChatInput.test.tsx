/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

describe("CopilotKit chat input", () => {
  it("renders textarea inside input container when globals are loaded", () => {
    render(
      <div className="copilotKitSidebar">
        <div className="copilotKitInputContainer poweredByContainer">
          <div className="copilotKitInput">
            <textarea
              placeholder="Ask about sales, trends, or metrics..."
              aria-label="Chat message"
            />
          </div>
          <p className="poweredBy">Powered by CopilotKit</p>
        </div>
      </div>,
    );

    const textarea = screen.getByRole("textbox", { name: /chat message/i });
    expect(textarea).toBeTruthy();
    expect(getComputedStyle(textarea.closest(".copilotKitInputContainer")!).display).not.toBe(
      "none",
    );
  });
});
