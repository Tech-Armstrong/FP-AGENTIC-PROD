/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import {
  FinancialPlanPanel,
  emptyAppliedRates,
  type PlanSummary,
  type PlanTab,
} from "../FinancialPlanPanel";
import type { EducationChildBlock } from "@/lib/educationPlanningView";
import type { PlanInputSnapshot } from "@/lib/planInputValidation";

const baseSummary: PlanSummary = {
  client_name: "Test Client",
  spending_behavior: { saving_ratio: 0.25, expense_ratio: 0.75, red_flag: false },
  liquidity_flag: "OK",
  flexibility: "Medium",
};

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

function renderPanel({
  planTabs = [],
  planOverrides = null,
  makePlanBlockReason = null,
  currentInputSnapshot = makeSnapshot(),
  onPlanComplete = vi.fn(),
}: {
  planTabs?: PlanTab[];
  planOverrides?: {
    epf_rate?: number;
    ppf_rate?: number;
    nps_rate?: number;
    mf_expected_return?: number;
    rsu_growth_rate?: number;
    desired_monthly_annuity?: number;
    retirement_age?: number;
  } | null;
  makePlanBlockReason?: string | null;
  currentInputSnapshot?: PlanInputSnapshot;
  onPlanComplete?: ReturnType<typeof vi.fn>;
} = {}) {
  return {
    onPlanComplete,
    ...render(
      <FinancialPlanPanel
        recordId="rec123"
        planOverrides={planOverrides}
        originalRates={emptyAppliedRates()}
        planTabs={planTabs}
        activeTabId={planTabs[0]?.id ?? null}
        onActiveTabChange={() => {}}
        onPlanComplete={onPlanComplete}
        educationBlocks={educationBlocks}
        educationTargets={currentInputSnapshot.educationTargets}
        desiredMonthlyAnnuity={currentInputSnapshot.desiredMonthlyAnnuity}
        onDesiredMonthlyAnnuityChange={() => {}}
        retirementAge={currentInputSnapshot.retirementAge}
        onRetirementAgeChange={() => {}}
        makePlanBlockReason={makePlanBlockReason}
        currentInputSnapshot={currentInputSnapshot}
      />,
    ),
  };
}

describe("FinancialPlanPanel Make plan gating", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ok: true,
          summary: baseSummary,
          workflow_state: { done: true },
        }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("disables Make plan when required inputs are incomplete", () => {
    renderPanel({
      makePlanBlockReason:
        "Fill all plan inputs before generating the plan: Desired monthly annuity.",
      currentInputSnapshot: makeSnapshot({ desiredMonthlyAnnuity: "" }),
    });

    const button = screen.getByRole("button", { name: /Make plan/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute(
      "title",
      "Fill all plan inputs before generating the plan: Desired monthly annuity.",
    );
  });

  it("creates a single Master Plan on the first successful run", async () => {
    const { onPlanComplete } = renderPanel();

    fireEvent.click(screen.getByRole("button", { name: /Make plan/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(fetch).toHaveBeenCalledWith(
        "/api/financial-plan/run",
        expect.objectContaining({ method: "POST" }),
      );
      expect(onPlanComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          label: "Master Plan",
          inputSnapshot: makeSnapshot(),
        }),
      );
    });
  });

  it("disables Make plan when nothing changed from the active tab", () => {
    const snapshot = makeSnapshot();
    renderPanel({
      planTabs: [
        {
          id: "plan-1",
          label: "Master Plan",
          overrides: null,
          appliedRates: emptyAppliedRates(),
          inputSnapshot: snapshot,
          summary: baseSummary,
        },
      ],
      makePlanBlockReason:
        "Change at least one input to create a new plan version.",
      currentInputSnapshot: snapshot,
    });

    expect(screen.getByRole("button", { name: /Make plan/i })).toBeDisabled();
  });

  it("creates Plan 2 when the active snapshot has changed", async () => {
    const { onPlanComplete } = renderPanel({
      planTabs: [
        {
          id: "plan-1",
          label: "Master Plan",
          overrides: null,
          appliedRates: emptyAppliedRates(),
          inputSnapshot: makeSnapshot(),
          summary: baseSummary,
        },
      ],
      planOverrides: { epf_rate: 0.09 },
      currentInputSnapshot: makeSnapshot({
        rates: {
          epf: "9.00",
          ppf: "7.10",
          nps: "10.00",
          mf: "12.00",
          rsu: "10.00",
        },
      }),
    });

    fireEvent.click(screen.getByRole("button", { name: /Make plan/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(onPlanComplete).toHaveBeenCalledWith(
        expect.objectContaining({
          label: "Plan 2",
          overrides: { epf_rate: 0.09 },
        }),
      );
    });
  });
});
