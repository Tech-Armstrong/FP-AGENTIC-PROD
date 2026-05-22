/** Shared chart styling helpers (Zod schemas live on BarChart/PieChart components). */

export function formatChartValue(value: number): string {
  return `₹${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export function getChartPalette(isDark: boolean): string[] {
  return isDark
    ? [
        "#2dd4bf",
        "#63b3ed",
        "#68d391",
        "#f6ad55",
        "#b794f4",
        "#fc8181",
        "#fbbf24",
        "#a78bfa",
      ]
    : [
        "#0f766e",
        "#4299e1",
        "#48bb78",
        "#ed8936",
        "#9f7aea",
        "#f56565",
        "#d69e2e",
        "#667eea",
      ];
}

export function getBrandAccent(isDark: boolean): string {
  return isDark ? "#2dd4bf" : "#0f766e";
}
