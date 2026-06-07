/** Default annual RSU share-price growth (matches planning workflow). */
export const DEFAULT_RSU_GROWTH_RATE = 0.1;

export type RsuVestingTrancheInput = {
  year: string | number;
  no_shares?: number | null;
  vesting?: number | null;
};

export type RsuMarketQuote = {
  price_usd: number;
  usd_to_inr_rate: number;
};

export type ProjectedRsuTranche = {
  year: number;
  shares: number;
  /** Spot or compounded USD (derived from INR / FX for display). */
  priceUsd: number;
  usdToInr: number;
  /** Rounded INR per share — matches backend `price_per_share_inr`. */
  pricePerShareInr: number;
  /** @deprecated Use pricePerShareInr */
  priceInr: number;
  /** Matches backend `tranche_value_inr`. */
  trancheValueInr: number;
};

export function roundRsu2(n: number): number {
  return Math.round(n * 100) / 100;
}

/**
 * Project per-tranche values using the same loop as allocations_nodes.py:
 * compound unrounded INR between vest years, round(price × shares, 2).
 */
export function projectRsuVestingTranches(
  schedule: RsuVestingTrancheInput[],
  quote: RsuMarketQuote,
  growthRateDecimal: number,
): ProjectedRsuTranche[] {
  const sorted = [...schedule].sort(
    (a, b) => Number(a.year) - Number(b.year),
  );
  const usdToInr = quote.usd_to_inr_rate;
  let prevPricePerShareInr: number | null = null;

  return sorted.map((tranche, i) => {
    const vestYear = Number(tranche.year);
    const shares = tranche.no_shares ?? 0;

    let pricePerShareInr: number;
    if (i === 0) {
      pricePerShareInr = quote.price_usd * usdToInr;
    } else {
      const prevYear = Number(sorted[i - 1].year);
      const yearsGap = vestYear - prevYear;
      if (yearsGap > 0 && prevPricePerShareInr != null) {
        pricePerShareInr =
          prevPricePerShareInr * (1 + growthRateDecimal) ** yearsGap;
      } else {
        pricePerShareInr = prevPricePerShareInr ?? quote.price_usd * usdToInr;
      }
    }
    prevPricePerShareInr = pricePerShareInr;

    const pricePerShareInrRounded = roundRsu2(pricePerShareInr);
    return {
      year: vestYear,
      shares,
      priceUsd: roundRsu2(pricePerShareInr / usdToInr),
      usdToInr,
      pricePerShareInr: pricePerShareInrRounded,
      priceInr: pricePerShareInrRounded,
      trancheValueInr: roundRsu2(pricePerShareInr * shares),
    };
  });
}

/** Sum tranche values and total portfolio (matches backend total_rsu_value_inr). */
export function sumProjectedRsuValue(rows: ProjectedRsuTranche[]): number {
  return roundRsu2(rows.reduce((s, r) => s + r.trancheValueInr, 0));
}
