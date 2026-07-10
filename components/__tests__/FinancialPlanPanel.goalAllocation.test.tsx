/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  FinancialPlanPanel,
  emptyAppliedRates,
  type PlanSummary,
  type PlanTab,
} from "../FinancialPlanPanel";
import type { EducationChildBlock } from "@/lib/educationPlanningView";
import type { PlanInputSnapshot } from "@/lib/planInputValidation";

const educationBlocks: EducationChildBlock[] = [
  {
    name: "Aarav",
    age: 10,
    airtableSlot: 1,
    hasPg: false,
    ug: {
      stream: "Engineering",
      destination: "Domestic",
      duration: 4,
      targetYear: 2034,
      startYear: 2030,
      endYear: 2034,
      currentCost: null,
      futureCost: null,
      corpusGap: null,
      status: null,
    },
    pg: null,
  },
];

const snapshot: PlanInputSnapshot = {
  rates: { epf: "8.50", ppf: "7.10", nps: "10.00", mf: "12.00", rsu: "10.00" },
  educationTargets: { Aarav: { ug: "2500000" } },
  desiredMonthlyAnnuity: "50000",
  retirementAge: "60",
};

function makeSummary(goalAllocationPreview: PlanSummary["goal_allocation_preview"]): PlanSummary {
  return {
    client_name: "Test Client",
    spending_behavior: { saving_ratio: 0.25, expense_ratio: 0.75, red_flag: false },
    liquidity_flag: "OK",
    flexibility: "Medium",
    goal_allocation_preview: goalAllocationPreview,
  };
}

function renderWithSummary(summary: PlanSummary) {
  const tab: PlanTab = {
    id: "tab-1",
    label: "Master Plan",
    summary,
    workflowState: { done: true },
    appliedRates: emptyAppliedRates(),
    inputSnapshot: snapshot,
  };

  return render(
    <FinancialPlanPanel
      recordId="rec123"
      planOverrides={null}
      originalRates={emptyAppliedRates()}
      planTabs={[tab]}
      activeTabId="tab-1"
      onActiveTabChange={() => {}}
      onPlanComplete={() => {}}
      educationBlocks={educationBlocks}
      educationTargets={snapshot.educationTargets}
      desiredMonthlyAnnuity={snapshot.desiredMonthlyAnnuity}
      onDesiredMonthlyAnnuityChange={() => {}}
      retirementAge={snapshot.retirementAge}
      onRetirementAgeChange={() => {}}
      makePlanBlockReason={null}
      currentInputSnapshot={snapshot}
    />,
  );
}

describe("FinancialPlanPanel goal allocation destination badge", () => {
  it("shows Domestic badge left of FUNDED for education goals", () => {
    renderWithSummary(
      makeSummary([
        {
          goal_name: "Asha UG",
          destination: "Domestic",
          target_corpus: 5_000_000,
          corpus_gap: 0,
          start_year: 2030,
          end_year: 2035,
          filter: [{ type: "funded" }],
        },
      ]),
    );

    expect(screen.getByText("Asha UG")).toBeInTheDocument();
    expect(screen.getByText("Domestic")).toBeInTheDocument();
    expect(screen.getByText("funded")).toBeInTheDocument();
  });

  it("does not show destination badge for retirement goals", () => {
    renderWithSummary(
      makeSummary([
        {
          goal_name: "Retirement",
          target_corpus: 10_000_000,
          corpus_gap: 0,
          target_year: 2045,
          filter: [{ type: "funded" }],
        },
      ]),
    );

    expect(screen.getByText("Retirement")).toBeInTheDocument();
    expect(screen.queryByText("Domestic")).not.toBeInTheDocument();
    expect(screen.queryByText("International")).not.toBeInTheDocument();
    expect(screen.getByText("funded")).toBeInTheDocument();
  });
});
