/**
 * @vitest-environment jsdom
 */
import React from "react";
import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider } from "../providers/ThemeProvider";
import {
  ChartTools,
  BAR_CHART_TOOL,
  PIE_CHART_TOOL,
  chartComponentConfigs,
  renderBarChartFromAgentArgs,
  renderPieChartFromAgentArgs,
} from "../ChartTools";
import { BarChartProps } from "../generative-ui/BarChart";
import { PieChartProps } from "../generative-ui/PieChart";

const useComponent = vi.fn();

vi.mock("@copilotkit/react-core/v2", () => ({
  useComponent: (config: unknown, deps?: unknown[]) => useComponent(config, deps),
}));

beforeAll(() => {
  class ResizeObserverMock {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  vi.stubGlobal("ResizeObserver", ResizeObserverMock);
});

function wrap(ui: React.ReactNode) {
  return render(
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
      {ui}
    </ThemeProvider>,
  );
}

describe("ChartTools useComponent registration", () => {
  beforeEach(() => {
    useComponent.mockClear();
  });

  it("registers barChart and pieChart with Zod schemas and component renderers", () => {
    wrap(<ChartTools />);
    expect(useComponent).toHaveBeenCalledTimes(2);

    const bar = useComponent.mock.calls[0][0] as {
      name: string;
      parameters: typeof BarChartProps;
      render: typeof import("../generative-ui/BarChart").BarChart;
      agentId: string;
    };
    const pie = useComponent.mock.calls[1][0] as typeof bar;

    expect(bar.name).toBe(BAR_CHART_TOOL);
    expect(pie.name).toBe(PIE_CHART_TOOL);
    expect(bar.parameters).toBe(BarChartProps);
    expect(pie.parameters).toBe(PieChartProps);
    expect(bar.render).toBe(chartComponentConfigs[0].render);
    expect(pie.render).toBe(chartComponentConfigs[1].render);
    expect(bar.agentId).toBe("dashboard_agent");

    expect(
      BarChartProps.safeParse({
        data: [{ label: "A", value: 1 }],
      }).success,
    ).toBe(true);
  });
});

describe("Agent pieChart tool call → inline chart (e2e render)", () => {
  it("renders PieChart in chat output when agent supplies pieChart args", () => {
    wrap(
      renderPieChartFromAgentArgs({
        title: "Portfolio mix",
        data: [
          { label: "Equity", value: 55 },
          { label: "Debt", value: 45 },
        ],
      }),
    );
    expect(screen.getByText("Portfolio mix")).toBeTruthy();
    expect(screen.getByText("Equity")).toBeTruthy();
    expect(document.querySelector(".recharts-pie")).toBeTruthy();
  });

  it("renders BarChart in chat output when agent supplies barChart args", () => {
    wrap(
      renderBarChartFromAgentArgs({
        title: "Goal amounts",
        data: [
          { label: "Retirement", value: 1000000 },
          { label: "Education", value: 500000 },
        ],
      }),
    );
    expect(screen.getByText("Goal amounts")).toBeTruthy();
    expect(document.querySelectorAll(".recharts-bar-rectangle").length).toBe(2);
  });
});
