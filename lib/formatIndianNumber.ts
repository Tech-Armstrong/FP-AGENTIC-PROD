const LAKH = 100_000;
const CRORE = 10_000_000;

export type FormatIndianNumberOptions = {
  /** Prepended when true or when input used ₹ (default: none). */
  currencySymbol?: string;
};

function trimFraction(value: string): string {
  if (!value.includes(".")) return value;
  return value.replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
}

function formatAbbreviatedMagnitude(value: number, divisor: number, suffix: string): string {
  const scaled = value / divisor;
  const rounded =
    scaled >= 100
      ? String(Math.round(scaled))
      : trimFraction(scaled.toFixed(2));
  return `${rounded}${suffix}`;
}

/**
 * Format a number for Indian financial UI.
 * - >= 1 crore → Cr (e.g. 7.5Cr)
 * - >= 1 lakh → L (e.g. 7L, 7.25L)
 * - below 1 lakh → en-IN digit grouping (e.g. 45,000) — no K suffix
 */
export function formatIndianNumber(
  value: number,
  options: FormatIndianNumberOptions = {},
): string {
  if (!Number.isFinite(value)) return String(value);

  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  const prefix = options.currencySymbol ?? "";

  let core: string;
  if (abs >= CRORE) {
    core = formatAbbreviatedMagnitude(abs, CRORE, "Cr");
  } else if (abs >= LAKH) {
    core = formatAbbreviatedMagnitude(abs, LAKH, "L");
  } else {
    core = new Intl.NumberFormat("en-IN", {
      maximumFractionDigits: 0,
    }).format(abs);
  }

  return `${sign}${prefix}${core}`;
}

/** Shorthand for monetary values shown in charts and tables. */
export function formatIndianCurrency(value: number): string {
  return formatIndianNumber(value, { currencySymbol: "₹" });
}

/**
 * Parse a table/markdown cell that looks like a monetary amount.
 * Returns null for years, percentages, IDs, or non-numeric prose.
 */
export function parseMonetaryCellText(text: string): {
  value: number;
  currencySymbol?: string;
} | null {
  const trimmed = text.trim();
  if (!trimmed || /%$/.test(trimmed)) return null;

  // Standalone 4-digit years
  if (/^\d{4}$/.test(trimmed)) {
    const y = Number(trimmed);
    if (y >= 1900 && y <= 2100) return null;
  }

  const match = trimmed.match(/^(₹|Rs\.?\s*)?([\d,]+(?:\.\d+)?)$/i);
  if (!match) return null;

  const currencySymbol = match[1]?.toLowerCase().startsWith("r") ? "₹" : match[1] || undefined;
  const value = Number(match[2].replace(/,/g, ""));
  if (!Number.isFinite(value)) return null;

  const hasCurrency = Boolean(match[1]);
  if (!hasCurrency && value >= 1900 && value <= 2100 && !trimmed.includes(",")) {
    return null;
  }
  // Small integers without currency (counts, IDs) — leave as-is
  if (!hasCurrency && Math.abs(value) < 10_000 && Number.isInteger(value)) {
    return null;
  }

  return { value, currencySymbol: hasCurrency ? "₹" : undefined };
}

/** Re-format a markdown table cell if it is clearly monetary. */
export function formatMonetaryCellText(text: string): string | null {
  const parsed = parseMonetaryCellText(text);
  if (!parsed) return null;
  return formatIndianNumber(parsed.value, {
    currencySymbol: parsed.currencySymbol,
  });
}

export function isNumericTableCell(text: string): boolean {
  const trimmed = text.trim();
  if (!trimmed) return false;
  if (formatMonetaryCellText(trimmed) !== null) return true;
  if (/^-?[\d,]+(\.\d+)?$/.test(trimmed)) {
    const n = Number(trimmed.replace(/,/g, ""));
    return Number.isFinite(n) && Math.abs(n) >= 10_000;
  }
  return false;
}
