/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeAll } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider } from "../providers/ThemeProvider";
import { PieChart } from "../generative-ui/PieChart";

beforeAll(() => {
  class ResizeObserverMock {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("ResizeObserver", ResizeObserverMock);
});

function renderChart(
  props: Parameters<typeof PieChart>[0],
  theme: "light" | "dark" = "light",
) {
  if (theme === "dark") document.documentElement.classList.add("dark");
  else document.documentElement.classList.remove("dark");
  return render(
    <ThemeProvider attribute="class" defaultTheme={theme} enableSystem={false}>
      <PieChart {...props} />
    </ThemeProvider>,
  );
}

describe("PieChart", () => {
  it("renders title, legend labels, and pie chart", () => {
    renderChart({
      title: "Asset allocation",
      data: [
        { label: "Equity", value: 60 },
        { label: "Debt", value: 40 },
      ],
    });
    expect(screen.getByText("Asset allocation")).toBeTruthy();
    expect(screen.getByText("Equity")).toBeTruthy();
    expect(screen.getByText("Debt")).toBeTruthy();
    expect(document.querySelector(".recharts-pie")).toBeTruthy();
  });

  it("shows empty state when data is empty", () => {
    renderChart({ data: [] });
    expect(screen.getByText(/No data to display/i)).toBeTruthy();
  });

  it("renders in dark mode", () => {
    renderChart(
      {
        data: [
          { label: "ULIP", value: 30 },
          { label: "MF", value: 70 },
        ],
      },
      "dark",
    );
    expect(screen.getByText("ULIP")).toBeTruthy();
  });
});
