import type { EducationChildBlock } from "@/lib/educationPlanningView";

export type PlanInputRates = {
  epf: string;
  ppf: string;
  nps: string;
  mf: string;
  rsu: string;
};

export type PlanInputSnapshot = {
  rates: PlanInputRates;
  educationTargets: Record<string, { ug?: string; pg?: string }>;
  desiredMonthlyAnnuity: string;
  retirementAge: string;
};

export type RequiredPlanFields = {
  rates: {
    epf: boolean;
    ppf: boolean;
    nps: boolean;
    mf: boolean;
    rsu: boolean;
  };
  educationChildNames: string[];
  educationPgRequired: Record<string, boolean>;
  annuity: true;
  retirementAge: true;
};

type ValidationDetail = {
  client_data?: {
    investment_details?: {
      retirement_investments?: {
        epf?: unknown[];
        ppf?: unknown[];
        nps?: unknown[];
      };
      mutual_funds?: unknown[];
      rsu?: unknown[];
    };
  };
};

export function parsePctInput(raw: string): number | null {
  const cleaned = raw.replace(/[%\s]/g, "").trim();
  if (!cleaned) return null;
  const n = Number(cleaned);
  return Number.isFinite(n) && n >= 0 ? n : null;
}

export function parseRateToDecimal(raw: string): number | null {
  const n = parsePctInput(raw);
  if (n === null) return null;
  return n > 1 ? n / 100 : n;
}

export function rateDecimalsMatch(a: number, b: number): boolean {
  return Math.round(a * 10000) === Math.round(b * 10000);
}

function parsePositiveAmount(raw: string): number | null {
  const cleaned = raw.trim();
  if (!cleaned) return null;
  const n = Number(cleaned);
  return Number.isFinite(n) && n > 0 ? n : null;
}

function parseRetirementAge(raw: string): number | null {
  const cleaned = raw.trim();
  if (!cleaned) return null;
  const n = Number(cleaned);
  if (!Number.isFinite(n)) return null;
  const rounded = Math.round(n);
  if (rounded < 40 || rounded > 80) return null;
  return rounded;
}

function trimTargetMap(
  targets: Record<string, { ug?: string; pg?: string }>,
): Record<string, { ug?: string; pg?: string }> {
  return Object.fromEntries(
    Object.entries(targets).map(([childName, value]) => [
      childName,
      {
        ug: value.ug?.trim(),
        pg: value.pg?.trim(),
      },
    ]),
  );
}

export function buildPlanInputSnapshot(inputs: PlanInputSnapshot): PlanInputSnapshot {
  return {
    rates: {
      epf: inputs.rates.epf.trim(),
      ppf: inputs.rates.ppf.trim(),
      nps: inputs.rates.nps.trim(),
      mf: inputs.rates.mf.trim(),
      rsu: inputs.rates.rsu.trim(),
    },
    educationTargets: trimTargetMap(inputs.educationTargets),
    desiredMonthlyAnnuity: inputs.desiredMonthlyAnnuity.trim(),
    retirementAge: inputs.retirementAge.trim(),
  };
}

export function deriveRequiredPlanFields(
  detail: ValidationDetail | null | undefined,
  educationBlocks: EducationChildBlock[] | undefined,
): RequiredPlanFields {
  const investmentDetails = detail?.client_data?.investment_details;
  const retirement = investmentDetails?.retirement_investments;
  const blocks = educationBlocks ?? [];

  return {
    rates: {
      epf: (retirement?.epf ?? []).length > 0,
      ppf: (retirement?.ppf ?? []).length > 0,
      nps: (retirement?.nps ?? []).length > 0,
      mf: (investmentDetails?.mutual_funds ?? []).length > 0,
      rsu: (investmentDetails?.rsu ?? []).length > 0,
    },
    educationChildNames: blocks.map((block) => block.name),
    educationPgRequired: Object.fromEntries(
      blocks.map((block) => [block.name, block.hasPg]),
    ),
    annuity: true,
    retirementAge: true,
  };
}

export function validatePlanInputsComplete(
  inputs: PlanInputSnapshot,
  required: RequiredPlanFields,
): { ok: boolean; missing: string[] } {
  const snapshot = buildPlanInputSnapshot(inputs);
  const missing: string[] = [];

  if (required.rates.epf && parseRateToDecimal(snapshot.rates.epf) === null) {
    missing.push("EPF rate");
  }
  if (required.rates.ppf && parseRateToDecimal(snapshot.rates.ppf) === null) {
    missing.push("PPF rate");
  }
  if (required.rates.nps && parseRateToDecimal(snapshot.rates.nps) === null) {
    missing.push("NPS rate");
  }
  if (required.rates.mf && parseRateToDecimal(snapshot.rates.mf) === null) {
    missing.push("Mutual fund return");
  }
  if (required.rates.rsu && parseRateToDecimal(snapshot.rates.rsu) === null) {
    missing.push("RSU growth rate");
  }
  if (required.annuity && parsePositiveAmount(snapshot.desiredMonthlyAnnuity) === null) {
    missing.push("Desired monthly annuity");
  }
  if (required.retirementAge && parseRetirementAge(snapshot.retirementAge) === null) {
    missing.push("Retirement age");
  }

  for (const childName of required.educationChildNames) {
    const target = snapshot.educationTargets[childName] ?? {};
    if (parsePositiveAmount(target.ug ?? "") === null) {
      missing.push(`${childName} UG target`);
    }
    if (
      required.educationPgRequired[childName] &&
      parsePositiveAmount(target.pg ?? "") === null
    ) {
      missing.push(`${childName} PG target`);
    }
  }

  return { ok: missing.length === 0, missing };
}

export function planInputsChanged(
  current: PlanInputSnapshot,
  frozen: PlanInputSnapshot,
  required: RequiredPlanFields,
): boolean {
  const currentSnapshot = buildPlanInputSnapshot(current);
  const frozenSnapshot = buildPlanInputSnapshot(frozen);

  const rateKeys: Array<keyof PlanInputRates> = ["epf", "ppf", "nps", "mf", "rsu"];
  for (const key of rateKeys) {
    if (!required.rates[key]) continue;
    const currentRate = parseRateToDecimal(currentSnapshot.rates[key]);
    const frozenRate = parseRateToDecimal(frozenSnapshot.rates[key]);
    if (currentRate === null || frozenRate === null) {
      if (currentSnapshot.rates[key] !== frozenSnapshot.rates[key]) return true;
      continue;
    }
    if (!rateDecimalsMatch(currentRate, frozenRate)) return true;
  }

  if (
    required.annuity &&
    currentSnapshot.desiredMonthlyAnnuity !== frozenSnapshot.desiredMonthlyAnnuity
  ) {
    return true;
  }
  if (
    required.retirementAge &&
    currentSnapshot.retirementAge !== frozenSnapshot.retirementAge
  ) {
    return true;
  }

  for (const childName of required.educationChildNames) {
    const currentTarget = currentSnapshot.educationTargets[childName] ?? {};
    const frozenTarget = frozenSnapshot.educationTargets[childName] ?? {};
    if ((currentTarget.ug ?? "") !== (frozenTarget.ug ?? "")) return true;
    if (
      required.educationPgRequired[childName] &&
      (currentTarget.pg ?? "") !== (frozenTarget.pg ?? "")
    ) {
      return true;
    }
  }

  return false;
}

export function nextPlanTabLabel(existingTabCount: number): string {
  return existingTabCount === 0 ? "Master Plan" : `Plan ${existingTabCount + 1}`;
}
