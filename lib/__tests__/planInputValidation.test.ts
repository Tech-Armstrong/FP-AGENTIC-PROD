import { describe, expect, it } from "vitest";
import type { EducationChildBlock } from "@/lib/educationPlanningView";
import {
  deriveRequiredPlanFields,
  nextPlanTabLabel,
  planInputsChanged,
  validatePlanInputsComplete,
  type PlanInputSnapshot,
} from "../planInputValidation";

function makeSnapshot(
  overrides: Partial<PlanInputSnapshot> = {},
): PlanInputSnapshot {
  return {
    rates: {
      epf: "8.50",
      ppf: "7.10",
      nps: "10.00",
      mf: "12.00",
      rsu: "10.00",
      ...(overrides.rates ?? {}),
    },
    educationTargets: {
      Aarav: { ug: "2500000", pg: "1800000" },
      ...(overrides.educationTargets ?? {}),
    },
    desiredMonthlyAnnuity: "50000",
    retirementAge: "60",
    ...overrides,
  };
}

const educationBlocks: EducationChildBlock[] = [
  {
    name: "Aarav",
    age: 10,
    hasPg: true,
    ug: {
      stream: "Engineering",
      destination: "India",
      duration: 4,
      targetYear: 2034,
      startYear: 2030,
      endYear: 2034,
      currentCost: null,
      futureCost: null,
      corpusGap: null,
      status: null,
    },
    pg: {
      stream: "MBA",
      destination: "India",
      duration: 2,
      targetYear: 2036,
      startYear: 2035,
      endYear: 2036,
      currentCost: null,
      futureCost: null,
      corpusGap: null,
      status: null,
    },
  },
];

describe("planInputValidation", () => {
  it("derives required fields from visible client sections", () => {
    const required = deriveRequiredPlanFields(
      {
        client_data: {
          investment_details: {
            retirement_investments: {
              epf: [{}],
              ppf: [],
              nps: [],
            },
            mutual_funds: [{}],
            rsu: [],
          },
        },
      },
      educationBlocks,
    );

    expect(required.rates).toEqual({
      epf: true,
      ppf: false,
      nps: false,
      mf: true,
      rsu: false,
    });
    expect(required.educationChildNames).toEqual(["Aarav"]);
    expect(required.educationPgRequired).toEqual({ Aarav: true });
    expect(required.annuity).toBe(true);
    expect(required.retirementAge).toBe(true);
  });

  it("reports missing required inputs and accepts pre-filled valid values", () => {
    const required = deriveRequiredPlanFields(
      {
        client_data: {
          investment_details: {
            retirement_investments: {
              epf: [{}],
              ppf: [{}],
              nps: [{}],
            },
            mutual_funds: [],
            rsu: [{}],
          },
        },
      },
      educationBlocks,
    );

    const missingAnnuity = validatePlanInputsComplete(
      makeSnapshot({ desiredMonthlyAnnuity: "" }),
      required,
    );
    expect(missingAnnuity.ok).toBe(false);
    expect(missingAnnuity.missing).toContain("Desired monthly annuity");

    const valid = validatePlanInputsComplete(makeSnapshot(), required);
    expect(valid.ok).toBe(true);
    expect(valid.missing).toEqual([]);
  });

  it("detects changes against the active tab snapshot", () => {
    const required = deriveRequiredPlanFields(
      {
        client_data: {
          investment_details: {
            retirement_investments: {
              epf: [{}],
              ppf: [{}],
              nps: [{}],
            },
            mutual_funds: [{}],
            rsu: [{}],
          },
        },
      },
      educationBlocks,
    );

    const base = makeSnapshot();
    expect(planInputsChanged(base, base, required)).toBe(false);

    expect(
      planInputsChanged(
        makeSnapshot({ rates: { ...base.rates, epf: "9.00" } }),
        base,
        required,
      ),
    ).toBe(true);

    expect(
      planInputsChanged(
        makeSnapshot({
          educationTargets: { Aarav: { ug: "2500000", pg: "2000000" } },
        }),
        base,
        required,
      ),
    ).toBe(true);
  });

  it("labels plan tabs from Master Plan onward", () => {
    expect(nextPlanTabLabel(0)).toBe("Master Plan");
    expect(nextPlanTabLabel(1)).toBe("Plan 2");
    expect(nextPlanTabLabel(2)).toBe("Plan 3");
  });
});
