import type { SpouseData } from "@/components/SpouseDetailsPanel";

export const SPOUSE_AIRTABLE_FIELD_KEYS = [
  "spouse_name",
  "spouse_dob",
  "spouse_investment_mutual_fund_value",
  "spouse_investment_direct_equity_value",
  "spouse_investment_vestd_esop",
  "spouse_investment_unvested_esop",
  "spouse_investment_pf_current_value",
  "spouse_investment_pf_contribution",
  "spouse_investment_fd_bond_invested_amount",
  "spouse_investment_fd_bond_rate_intrest",
  "spouse_investment_fd_bond_maturity_date",
] as const;

export type SpouseAirtableFieldKey = (typeof SPOUSE_AIRTABLE_FIELD_KEYS)[number];

export type SpouseUiFieldPath =
  | "spouse_name"
  | "spouse_dob"
  | "spouse_investment_mutual_fund_value"
  | "spouse_investment_direct_equity_value"
  | "esop.vested"
  | "esop.unvested"
  | "provident_fund.current_value"
  | "provident_fund.monthly_contribution"
  | "fd_bond.invested_amount"
  | "fd_bond.interest_rate"
  | "fd_bond.maturity_date";

const UI_PATH_TO_AIRTABLE: Record<SpouseUiFieldPath, SpouseAirtableFieldKey> = {
  spouse_name: "spouse_name",
  spouse_dob: "spouse_dob",
  spouse_investment_mutual_fund_value: "spouse_investment_mutual_fund_value",
  spouse_investment_direct_equity_value: "spouse_investment_direct_equity_value",
  "esop.vested": "spouse_investment_vestd_esop",
  "esop.unvested": "spouse_investment_unvested_esop",
  "provident_fund.current_value": "spouse_investment_pf_current_value",
  "provident_fund.monthly_contribution": "spouse_investment_pf_contribution",
  "fd_bond.invested_amount": "spouse_investment_fd_bond_invested_amount",
  "fd_bond.interest_rate": "spouse_investment_fd_bond_rate_intrest",
  "fd_bond.maturity_date": "spouse_investment_fd_bond_maturity_date",
};

const TEXT_FIELDS = new Set<SpouseAirtableFieldKey>([
  "spouse_name",
  "spouse_dob",
  "spouse_investment_fd_bond_maturity_date",
]);

const RATE_FIELDS = new Set<SpouseAirtableFieldKey>([
  "spouse_investment_fd_bond_rate_intrest",
]);

const NUMERIC_FIELDS = new Set<SpouseAirtableFieldKey>(
  SPOUSE_AIRTABLE_FIELD_KEYS.filter(
    (key) => !TEXT_FIELDS.has(key) && !RATE_FIELDS.has(key),
  ),
);

export function uiPathToAirtableKey(uiPath: SpouseUiFieldPath): SpouseAirtableFieldKey {
  return UI_PATH_TO_AIRTABLE[uiPath];
}

export function parseSpouseFieldValue(
  airtableKey: SpouseAirtableFieldKey,
  rawValue: string,
): string | number | null {
  const trimmed = rawValue.trim();
  if (TEXT_FIELDS.has(airtableKey)) {
    return trimmed;
  }
  if (trimmed === "") {
    return null;
  }
  const parsed = Number(trimmed);
  if (Number.isNaN(parsed)) {
    throw new Error(`Invalid number for ${airtableKey}`);
  }
  return parsed;
}

export function flattenSpouseFieldToAirtable(
  uiPath: SpouseUiFieldPath,
  rawValue: string,
): Partial<Record<SpouseAirtableFieldKey, string | number | null>> {
  const airtableKey = uiPathToAirtableKey(uiPath);
  return { [airtableKey]: parseSpouseFieldValue(airtableKey, rawValue) };
}

export function flattenSpousePatchToAirtable(
  patch: Partial<SpouseData>,
): Record<string, string | number | null> {
  const out: Record<string, string | number | null> = {};

  const flatKeys = [
    "spouse_name",
    "spouse_dob",
    "spouse_investment_mutual_fund_value",
    "spouse_investment_direct_equity_value",
  ] as const;

  for (const key of flatKeys) {
    if (key in patch) {
      const value = patch[key];
      if (value == null || value === "") {
        out[key] = TEXT_FIELDS.has(key) ? "" : null;
      } else if (typeof value === "number") {
        out[key] = value;
      } else {
        out[key] = String(value);
      }
    }
  }

  if (patch.esop) {
    if ("vested" in patch.esop) {
      out.spouse_investment_vestd_esop =
        patch.esop.vested == null ? null : Number(patch.esop.vested);
    }
    if ("unvested" in patch.esop) {
      out.spouse_investment_unvested_esop =
        patch.esop.unvested == null ? null : Number(patch.esop.unvested);
    }
  }

  if (patch.provident_fund) {
    if ("current_value" in patch.provident_fund) {
      out.spouse_investment_pf_current_value =
        patch.provident_fund.current_value == null
          ? null
          : Number(patch.provident_fund.current_value);
    }
    if ("monthly_contribution" in patch.provident_fund) {
      out.spouse_investment_pf_contribution =
        patch.provident_fund.monthly_contribution == null
          ? null
          : Number(patch.provident_fund.monthly_contribution);
    }
  }

  if (patch.fd_bond) {
    if ("invested_amount" in patch.fd_bond) {
      out.spouse_investment_fd_bond_invested_amount =
        patch.fd_bond.invested_amount == null ? null : Number(patch.fd_bond.invested_amount);
    }
    if ("interest_rate" in patch.fd_bond) {
      const rate = patch.fd_bond.interest_rate;
      out.spouse_investment_fd_bond_rate_intrest =
        rate == null ? null : Number(rate) * 100;
    }
    if ("maturity_date" in patch.fd_bond) {
      out.spouse_investment_fd_bond_maturity_date =
        patch.fd_bond.maturity_date == null ? "" : String(patch.fd_bond.maturity_date);
    }
  }

  return out;
}

export function spouseValueToInput(uiPath: SpouseUiFieldPath, spouse: SpouseData): string {
  if (uiPath === "spouse_name") return spouse.spouse_name ?? "";
  if (uiPath === "spouse_dob") return spouse.spouse_dob ?? "";
  if (uiPath === "spouse_investment_mutual_fund_value") {
    return spouse.spouse_investment_mutual_fund_value != null
      ? String(spouse.spouse_investment_mutual_fund_value)
      : "";
  }
  if (uiPath === "spouse_investment_direct_equity_value") {
    return spouse.spouse_investment_direct_equity_value != null
      ? String(spouse.spouse_investment_direct_equity_value)
      : "";
  }
  if (uiPath === "esop.vested") {
    return spouse.esop?.vested != null ? String(spouse.esop.vested) : "";
  }
  if (uiPath === "esop.unvested") {
    return spouse.esop?.unvested != null ? String(spouse.esop.unvested) : "";
  }
  if (uiPath === "provident_fund.current_value") {
    return spouse.provident_fund?.current_value != null
      ? String(spouse.provident_fund.current_value)
      : "";
  }
  if (uiPath === "provident_fund.monthly_contribution") {
    return spouse.provident_fund?.monthly_contribution != null
      ? String(spouse.provident_fund.monthly_contribution)
      : "";
  }
  if (uiPath === "fd_bond.invested_amount") {
    return spouse.fd_bond?.invested_amount != null
      ? String(spouse.fd_bond.invested_amount)
      : "";
  }
  if (uiPath === "fd_bond.interest_rate") {
    const rate = spouse.fd_bond?.interest_rate;
    return rate != null
      ? String(Number((Number(rate) * 100).toFixed(4)))
      : "";
  }
  if (uiPath === "fd_bond.maturity_date") {
    return spouse.fd_bond?.maturity_date != null ? String(spouse.fd_bond.maturity_date) : "";
  }
  return "";
}

export function valuesEqualForPath(uiPath: SpouseUiFieldPath, a: string, b: string): boolean {
  if (uiPath === "fd_bond.interest_rate") {
    const na = a.trim() === "" ? null : Number(a);
    const nb = b.trim() === "" ? null : Number(b);
    if (na == null && nb == null) return true;
    if (na == null || nb == null) return false;
    return Math.abs(na - nb) < 0.0001;
  }
  return a.trim() === b.trim();
}

export const ALL_SPOUSE_UI_PATHS: SpouseUiFieldPath[] = [
  "spouse_name",
  "spouse_dob",
  "spouse_investment_mutual_fund_value",
  "spouse_investment_direct_equity_value",
  "esop.vested",
  "esop.unvested",
  "provident_fund.current_value",
  "provident_fund.monthly_contribution",
  "fd_bond.invested_amount",
  "fd_bond.interest_rate",
  "fd_bond.maturity_date",
];
