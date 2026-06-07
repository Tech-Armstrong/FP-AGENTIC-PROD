import { describe, expect, it } from "vitest";
import {
  DEFAULT_RSU_GROWTH_RATE,
  projectRsuVestingTranches,
  roundRsu2,
  sumProjectedRsuValue,
} from "../rsuProjection";

const quote = { price_usd: 95, usd_to_inr_rate: 83 };

describe("projectRsuVestingTranches", () => {
  it("compounds INR per share 10% per year (Python parity)", () => {
    const rows = projectRsuVestingTranches(
      [
        { year: "2026", no_shares: 100 },
        { year: "2027", no_shares: 50 },
        { year: "2028", no_shares: 25 },
      ],
      quote,
      DEFAULT_RSU_GROWTH_RATE,
    );

    expect(rows).toHaveLength(3);
    const p0 = 95 * 83;
    const p1 = p0 * 1.1;
    const p2 = p1 * 1.1;

    expect(rows[0].pricePerShareInr).toBe(roundRsu2(p0));
    expect(rows[1].pricePerShareInr).toBe(roundRsu2(p1));
    expect(rows[2].pricePerShareInr).toBe(roundRsu2(p2));
    expect(rows[0].trancheValueInr).toBe(roundRsu2(p0 * 100));
    expect(rows[1].trancheValueInr).toBe(roundRsu2(p1 * 50));
    expect(rows[2].trancheValueInr).toBe(roundRsu2(p2 * 25));
    expect(rows[1].priceUsd).toBe(roundRsu2(p1 / 83));
  });

  it("matches Amazon AMZN backend rsu_portfolio golden values", () => {
    const amznQuote = { price_usd: 274, usd_to_inr_rate: 95.4331 };
    const rows = projectRsuVestingTranches(
      [
        { year: 2026, no_shares: 41 },
        { year: 2027, no_shares: 163 },
        { year: 2028, no_shares: 408 },
        { year: 2029, no_shares: 408 },
      ],
      amznQuote,
      0.1,
    );

    expect(rows[0].pricePerShareInr).toBe(26148.67);
    expect(rows[0].trancheValueInr).toBe(1072095.45);
    expect(rows[1].pricePerShareInr).toBe(28763.54);
    expect(rows[1].trancheValueInr).toBe(4688456.42);
    expect(rows[2].pricePerShareInr).toBe(31639.89);
    expect(rows[2].trancheValueInr).toBe(12909075.11);
    expect(rows[3].pricePerShareInr).toBe(34803.88);
    expect(rows[3].trancheValueInr).toBe(14199982.62);
    expect(sumProjectedRsuValue(rows)).toBe(32869609.6);
    expect(rows[0].trancheValueInr).toBe(1072095.45);
  });

  it("sorts tranches by year before projecting", () => {
    const rows = projectRsuVestingTranches(
      [
        { year: "2028", no_shares: 1 },
        { year: "2026", no_shares: 1 },
      ],
      quote,
      0.1,
    );
    expect(rows[0].year).toBe(2026);
    expect(rows[1].year).toBe(2028);
    expect(rows[1].pricePerShareInr).toBe(roundRsu2(95 * 83 * 1.1 ** 2));
  });
});
