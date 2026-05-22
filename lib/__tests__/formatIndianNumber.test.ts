import { describe, it, expect } from "vitest";
import {
  formatIndianNumber,
  formatIndianCurrency,
  formatMonetaryCellText,
  parseMonetaryCellText,
} from "../formatIndianNumber";

describe("formatIndianNumber", () => {
  it("abbreviates lakh and crore", () => {
    expect(formatIndianNumber(700_000)).toBe("7L");
    expect(formatIndianNumber(1_000_000)).toBe("10L");
    expect(formatIndianNumber(10_000_000)).toBe("1Cr");
    expect(formatIndianNumber(75_000_000)).toBe("7.5Cr");
    expect(formatIndianNumber(7_250_000)).toBe("72.5L");
  });

  it("keeps sub-lakh values as en-IN grouped digits", () => {
    expect(formatIndianNumber(45_000)).toBe("45,000");
    expect(formatIndianNumber(1_000)).toBe("1,000");
    expect(formatIndianNumber(999)).toBe("999");
  });

  it("trims unnecessary decimals", () => {
    expect(formatIndianNumber(7_000_000)).toBe("70L");
    expect(formatIndianNumber(7_500_000)).toBe("75L");
  });

  it("preserves currency symbol", () => {
    expect(formatIndianCurrency(700_000)).toBe("₹7L");
    expect(formatIndianCurrency(75_000_000)).toBe("₹7.5Cr");
    expect(formatIndianCurrency(45_000)).toBe("₹45,000");
  });

  it("handles negative values", () => {
    expect(formatIndianCurrency(-700_000)).toBe("-₹7L");
  });
});

describe("parseMonetaryCellText / formatMonetaryCellText", () => {
  it("does not treat years, percentages, or IDs as money", () => {
    expect(parseMonetaryCellText("2026")).toBeNull();
    expect(parseMonetaryCellText("12.5%")).toBeNull();
    expect(parseMonetaryCellText("rec_abc123")).toBeNull();
    expect(formatMonetaryCellText("2026")).toBeNull();
  });

  it("formats monetary table cells", () => {
    expect(formatMonetaryCellText("₹7,00,000")).toBe("₹7L");
    expect(formatMonetaryCellText("700000")).toBe("7L");
    expect(formatMonetaryCellText("45,000")).toBe("45,000");
  });
});
