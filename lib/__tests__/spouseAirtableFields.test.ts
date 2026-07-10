import { describe, expect, it } from "vitest";
import {
  ALL_SPOUSE_UI_PATHS,
  flattenSpouseFieldToAirtable,
  flattenSpousePatchToAirtable,
  parseSpouseFieldValue,
  spouseValueToInput,
  uiPathToAirtableKey,
  valuesEqualForPath,
} from "@/lib/spouseAirtableFields";
import type { SpouseData } from "@/components/SpouseDetailsPanel";

describe("spouseAirtableFields", () => {
  it("maps all UI paths to Airtable keys", () => {
    expect(uiPathToAirtableKey("esop.vested")).toBe("spouse_investment_vestd_esop");
    expect(uiPathToAirtableKey("fd_bond.interest_rate")).toBe(
      "spouse_investment_fd_bond_rate_intrest",
    );
    expect(ALL_SPOUSE_UI_PATHS).toHaveLength(11);
  });

  it("flattens a single field patch", () => {
    expect(flattenSpouseFieldToAirtable("spouse_name", "Jane Doe")).toEqual({
      spouse_name: "Jane Doe",
    });
    expect(flattenSpouseFieldToAirtable("spouse_investment_mutual_fund_value", "5000000")).toEqual({
      spouse_investment_mutual_fund_value: 5_000_000,
    });
  });

  it("writes interest rate as percent for Airtable", () => {
    expect(parseSpouseFieldValue("spouse_investment_fd_bond_rate_intrest", "8.5")).toBe(8.5);
    expect(flattenSpouseFieldToAirtable("fd_bond.interest_rate", "8.5")).toEqual({
      spouse_investment_fd_bond_rate_intrest: 8.5,
    });
  });

  it("flattens nested spouse patch with rate conversion", () => {
    const patch: Partial<SpouseData> = {
      esop: { vested: 1_000_000, unvested: 500_000 },
      fd_bond: { interest_rate: 0.085, invested_amount: 200_000 },
    };
    expect(flattenSpousePatchToAirtable(patch)).toEqual({
      spouse_investment_vestd_esop: 1_000_000,
      spouse_investment_unvested_esop: 500_000,
      spouse_investment_fd_bond_invested_amount: 200_000,
      spouse_investment_fd_bond_rate_intrest: 8.5,
    });
  });

  it("detects unchanged percent values", () => {
    const spouse: SpouseData = { fd_bond: { interest_rate: 0.085 } };
    const input = spouseValueToInput("fd_bond.interest_rate", spouse);
    expect(valuesEqualForPath("fd_bond.interest_rate", input, input)).toBe(true);
    expect(valuesEqualForPath("fd_bond.interest_rate", input, "8.5000")).toBe(true);
    expect(valuesEqualForPath("fd_bond.interest_rate", input, "9")).toBe(false);
  });
});
