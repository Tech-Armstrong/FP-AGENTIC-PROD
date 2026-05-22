/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { ThemeProvider } from "../providers/ThemeProvider";
import { ChatMarkdown } from "../ChatMarkdown";

const TABLE_MD = `
| Goal | Amount |
|------|-------:|
| Retirement | ₹7,00,000 |
| Education | 45000 |
| Year | 2026 |
`;

function renderMd(content: string, theme: "light" | "dark" = "light") {
  if (theme === "dark") document.documentElement.classList.add("dark");
  else document.documentElement.classList.remove("dark");
  return render(
    <ThemeProvider attribute="class" defaultTheme={theme} enableSystem={false}>
      <ChatMarkdown content={content} />
    </ThemeProvider>,
  );
}

describe("ChatMarkdown tables", () => {
  it("renders an HTML table with scroll wrapper", () => {
    const { container } = renderMd(TABLE_MD);
    expect(container.querySelector(".chat-markdown-table-wrap")).toBeTruthy();
    expect(container.querySelector("table.chat-markdown-table")).toBeTruthy();
    expect(container.querySelector("thead")).toBeTruthy();
  });

  it("right-aligns numeric columns with tabular figures", () => {
    const { container } = renderMd(TABLE_MD);
    const cells = container.querySelectorAll("td");
    const amountCell = Array.from(cells).find((c) =>
      c.textContent?.includes("7L"),
    );
    expect(amountCell?.className).toMatch(/text-right/);
    expect(amountCell?.className).toMatch(/tabular-nums/);
    const yearCell = Array.from(cells).find((c) => c.textContent?.includes("2026"));
    expect(yearCell?.className).toMatch(/text-left/);
  });

  it("abbreviates monetary cells via formatIndianNumber", () => {
    renderMd(TABLE_MD);
    expect(screen.getByText("₹7L")).toBeTruthy();
    expect(screen.getByText("45,000")).toBeTruthy();
    expect(screen.getByText("2026")).toBeTruthy();
  });

  it("renders in dark mode without error", () => {
    const { container } = renderMd(TABLE_MD, "dark");
    expect(container.querySelector("table")).toBeTruthy();
  });
});
