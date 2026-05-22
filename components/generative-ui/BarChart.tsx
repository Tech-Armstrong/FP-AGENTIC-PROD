"use client";

import { useMemo } from "react";
import { useTheme } from "next-themes";
import { z } from "zod";
import {
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatChartValue, getBrandAccent } from "@/lib/chartTools";
import { ChartEmptyState } from "./ChartToolShell";

export const chartDatumSchema = z.object({
  label: z.string(),
  value: z.coerce.number().finite(),
});

/** Zod schema for useComponent — must match agent tool args. */
export const BarChartProps = z.object({
  title: z.string().optional(),
  data: z.array(chartDatumSchema),
  xAxisLabel: z.string().optional(),
  yAxisLabel: z.string().optional(),
});

export type BarChartComponentProps = z.infer<typeof BarChartProps>;

export function BarChart({
  title,
  data,
  xAxisLabel,
  yAxisLabel,
}: BarChartComponentProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  const accent = getBrandAccent(isDark);
  const tickColor = isDark ? "#94a3b8" : "#64748b";
  const gridColor = isDark ? "#2d3748" : "#e4e9ef";

  const rows = useMemo(
    () =>
      (data ?? [])
        .filter((d) => d && typeof d.label === "string" && Number.isFinite(d.value))
        .map((d) => ({ label: d.label, value: d.value })),
    [data],
  );

  if (!rows.length) {
    return (
      <div className="w-full max-w-full overflow-hidden rounded-lg border border-[var(--border-subtle)] bg-[var(--surface)] p-3 shadow-sm dark:border-gray-700">
        {title ? (
          <h4 className="mb-2 text-sm font-semibold text-[var(--heading)]">{title}</h4>
        ) : null}
        <ChartEmptyState />
      </div>
    );
  }

  return (
    <div className="w-full max-w-full overflow-hidden rounded-lg border border-[var(--border-subtle)] bg-[var(--surface)] p-3 shadow-sm dark:border-gray-700">
      {title ? (
        <h4 className="mb-2 text-sm font-semibold text-[var(--heading)]">{title}</h4>
      ) : null}
      <div className="h-[220px] w-full min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsBarChart
            data={rows}
            margin={{ top: 8, right: 8, left: 4, bottom: xAxisLabel ? 28 : 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} />
            <XAxis
              dataKey="label"
              tick={{ fill: tickColor, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              interval={0}
              angle={rows.length > 5 ? -25 : 0}
              textAnchor={rows.length > 5 ? "end" : "middle"}
              height={rows.length > 5 ? 56 : 32}
              label={
                xAxisLabel
                  ? {
                      value: xAxisLabel,
                      position: "insideBottom",
                      offset: -4,
                      fill: tickColor,
                      fontSize: 11,
                    }
                  : undefined
              }
            />
            <YAxis
              tick={{ fill: tickColor, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => formatChartValue(Number(v))}
              width={72}
              label={
                yAxisLabel
                  ? {
                      value: yAxisLabel,
                      angle: -90,
                      position: "insideLeft",
                      fill: tickColor,
                      fontSize: 11,
                    }
                  : undefined
              }
            />
            <Tooltip
              cursor={{ fill: isDark ? "rgba(45,212,191,0.08)" : "rgba(15,118,110,0.08)" }}
              formatter={(value: number) => [formatChartValue(value), ""]}
              labelFormatter={(label) => String(label)}
              contentStyle={{
                backgroundColor: isDark ? "#1a2029" : "#ffffff",
                border: `1px solid ${isDark ? "#2d3748" : "#e4e9ef"}`,
                borderRadius: "8px",
                fontSize: "12px",
                color: isDark ? "#cbd5e1" : "#334155",
              }}
            />
            <Bar
              dataKey="value"
              fill={accent}
              radius={[4, 4, 0, 0]}
              maxBarSize={48}
              name="Value"
            />
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
