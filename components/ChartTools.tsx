"use client";

/**
 * Controlled generative UI: barChart / pieChart via CopilotKit v2 useComponent.
 * Registers frontend tools (forwarded to the agent by CopilotKitMiddleware) and
 * renders pre-built chart components when the model calls these tools.
 */

import { z } from "zod";
import { useComponent } from "@copilotkit/react-core/v2";
import { BarChart, BarChartProps } from "./generative-ui/BarChart";
import { PieChart, PieChartProps } from "./generative-ui/PieChart";
import { LANGGRAPH_AGENT_ID } from "@/lib/langgraph-agent";

export const BAR_CHART_TOOL = "barChart";
export const PIE_CHART_TOOL = "pieChart";

/** Mirrors useComponent registrations (for tests). */
export const chartComponentConfigs = [
  {
    name: BAR_CHART_TOOL,
    description:
      "Controlled generative UI that displays data as a bar chart for comparing values across categories.",
    parameters: BarChartProps,
    render: BarChart,
    agentId: LANGGRAPH_AGENT_ID,
  },
  {
    name: PIE_CHART_TOOL,
    description:
      "Controlled generative UI that displays data as a pie chart for parts-of-a-whole breakdowns.",
    parameters: PieChartProps,
    render: PieChart,
    agentId: LANGGRAPH_AGENT_ID,
  },
] as const;

/** Simulates agent tool-call args rendering inline in chat (useComponent render path). */
export function renderBarChartFromAgentArgs(args: z.infer<typeof BarChartProps>) {
  return <BarChart {...args} />;
}

export function renderPieChartFromAgentArgs(args: z.infer<typeof PieChartProps>) {
  return <PieChart {...args} />;
}

export function ChartTools() {
  useComponent(
    {
      name: BAR_CHART_TOOL,
      description: chartComponentConfigs[0].description,
      parameters: BarChartProps,
      render: BarChart,
      agentId: LANGGRAPH_AGENT_ID,
    },
    [],
  );

  useComponent(
    {
      name: PIE_CHART_TOOL,
      description: chartComponentConfigs[1].description,
      parameters: PieChartProps,
      render: PieChart,
      agentId: LANGGRAPH_AGENT_ID,
    },
    [],
  );

  return null;
}
