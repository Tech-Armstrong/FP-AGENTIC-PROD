/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider } from "../providers/ThemeProvider";
import { BarChart } from "../generative-ui/BarChart";

beforeAll(() => {
  class ResizeObserverMock {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("ResizeObserver", ResizeObserverMock);
});

function renderChart(
  props: Parameters<typeof BarChart>[0],
  theme: "light" | "dark" = "light",
) {
  if (theme === "dark") document.documentElement.classList.add("dark");
  else document.documentElement.classList.remove("dark");
  return render(
    <ThemeProvider attribute="class" defaultTheme={theme} enableSystem={false}>
      <BarChart {...props} />
    </ThemeProvider>,
  );
}

describe("BarChart", () => {
  it("renders title, labels, and bar segments", () => {
    renderChart({
      title: "Goal amounts",
      data: [
        { label: "Retirement", value: 1200000 },
        { label: "Education", value: 800000 },
      ],
    });
    expect(screen.getByText("Goal amounts")).toBeTruthy();
    expect(screen.getAllByText("Retirement").length).toBeGreaterThan(0);
    expect(document.querySelectorAll(".recharts-bar-rectangle").length).toBe(2);
  });

  it("shows empty state when data is empty", () => {
    renderChart({ data: [] });
    expect(screen.getByText(/No data to display/i)).toBeTruthy();
  });

  it("renders in dark mode", () => {
    renderChart({ data: [{ label: "EPF", value: 50000 }] }, "dark");
    expect(screen.getAllByText("EPF").length).toBeGreaterThan(0);
    expect(document.querySelector(".recharts-bar-rectangle")).toBeTruthy();
  });
});
