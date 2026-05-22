"use client";

import { useMemo } from "react";
import { useTheme } from "next-themes";
import { z } from "zod";
import {
  Cell,
  Legend,
  Pie,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { chartDatumSchema } from "./BarChart";
import { formatChartValue, getChartPalette } from "@/lib/chartTools";
import { ChartEmptyState } from "./ChartToolShell";

/** Zod schema for useComponent — must match agent tool args. */
export const PieChartProps = z.object({
  title: z.string().optional(),
  data: z.array(chartDatumSchema),
});

export type PieChartComponentProps = z.infer<typeof PieChartProps>;

const RADIAN = Math.PI / 180;

function renderPercentLabel(props: {
  cx?: number;
  cy?: number;
  midAngle?: number;
  innerRadius?: number;
  outerRadius?: number;
  percent?: number;
}) {
  const {
    cx = 0,
    cy = 0,
    midAngle = 0,
    innerRadius = 0,
    outerRadius = 0,
    percent = 0,
  } = props;
  if (percent < 0.06) return null;
  const radius =
    Number(innerRadius) + (Number(outerRadius) - Number(innerRadius)) * 0.55;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={11}
      fontWeight={600}
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
}

export function PieChart({ title, data }: PieChartComponentProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  const palette = getChartPalette(isDark);

  const rows = useMemo(() => {
    const valid = (data ?? []).filter(
      (d) => d && typeof d.label === "string" && Number.isFinite(d.value) && d.value > 0,
    );
    if (!valid.length) return [];
    return valid.map((d) => ({ name: d.label, value: d.value }));
  }, [data]);

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
      <div className="h-[240px] w-full min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsPieChart>
            <Pie
              data={rows}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="45%"
              innerRadius="52%"
              outerRadius="78%"
              paddingAngle={2}
              label={renderPercentLabel}
              labelLine={false}
            >
              {rows.map((_, i) => (
                <Cell key={`cell-${i}`} fill={palette[i % palette.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, _name, item) => {
                const payload = item?.payload as { name?: string } | undefined;
                const total = rows.reduce((s, r) => s + r.value, 0);
                const pct =
                  total > 0 ? ((Number(value) / total) * 100).toFixed(1) : "0";
                return [
                  `${formatChartValue(Number(value))} (${pct}%)`,
                  payload?.name ?? "",
                ];
              }}
              contentStyle={{
                backgroundColor: isDark ? "#1a2029" : "#ffffff",
                border: `1px solid ${isDark ? "#2d3748" : "#e4e9ef"}`,
                borderRadius: "8px",
                fontSize: "12px",
                color: isDark ? "#cbd5e1" : "#334155",
              }}
            />
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              align="center"
              iconType="circle"
              iconSize={8}
              formatter={(value) => (
                <span style={{ color: isDark ? "#94a3b8" : "#64748b", fontSize: "0.75rem" }}>
                  {value}
                </span>
              )}
            />
          </RechartsPieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
