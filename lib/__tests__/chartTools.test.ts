import { describe, it, expect } from "vitest";
import { BarChartProps } from "../../components/generative-ui/BarChart";
import { PieChartProps } from "../../components/generative-ui/PieChart";

describe("chart Zod prop schemas", () => {
  it("validates BarChartProps", () => {
    const r = BarChartProps.safeParse({
      title: "Goals",
      data: [{ label: "Retirement", value: 100000 }],
    });
    expect(r.success).toBe(true);
  });

  it("validates PieChartProps", () => {
    const r = PieChartProps.safeParse({
      data: [{ label: "Equity", value: 60 }],
    });
    expect(r.success).toBe(true);
  });
});
