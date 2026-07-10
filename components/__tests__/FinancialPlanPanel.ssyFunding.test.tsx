/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
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

describe("FinancialPlanPanel SSY funding card", () => {
  it("renders SSY as a card with amount instead of a sparse table row", () => {
    const { container } = renderWithSummary(
      makeSummary([
        {
          goal_name: "Ananya UG",
          target_corpus: 5_000_000,
          corpus_gap: 0,
          start_year: 2030,
          end_year: 2035,
          filter: [{ type: "funded" }],
          funded_from_preview: [
            {
              type: "SSY",
              amount: 500_000,
              source: "SSY account of Ananya",
            },
          ],
        },
      ]),
    );

    expect(screen.getByText("SSY")).toBeInTheDocument();
    expect(screen.getByText("Ananya")).toBeInTheDocument();
    expect(screen.getByText("₹5,00,000")).toBeInTheDocument();
    const ssyCard = screen.getByText("SSY").closest("div.rounded-lg");
    expect(ssyCard).toBeTruthy();
    expect(ssyCard!.className).toContain("w-fit");
    const amountUtilizedLabel = within(ssyCard!).getByText("Amount utilized");
    expect(amountUtilizedLabel).toBeInTheDocument();
    expect(amountUtilizedLabel.nextElementSibling?.textContent).toBe("₹5,00,000");

    const headerRow = screen.getByText("Ananya").parentElement;
    expect(headerRow?.textContent?.indexOf("Ananya")).toBeLessThan(
      headerRow?.textContent?.indexOf("SSY") ?? -1,
    );
    expect(within(ssyCard!).queryByText("From")).not.toBeInTheDocument();
    expect(within(ssyCard!).queryByText("Rate")).not.toBeInTheDocument();

    expect(screen.getByText("SSY").closest("table")).toBeNull();
    expect(container.querySelectorAll("table").length).toBe(0);
  });

  it("still renders SIP rows in the standard table format", () => {
    const { container } = renderWithSummary(
      makeSummary([
        {
          goal_name: "Ananya UG",
          target_corpus: 5_000_000,
          corpus_gap: 100_000,
          start_year: 2030,
          end_year: 2035,
          filter: [{ type: "partial_funded" }],
          funded_from_preview: [
            {
              type: "SSY",
              amount: 500_000,
              source: "SSY account of Ananya",
            },
            {
              type: "SIP",
              monthly: 25_000,
              from_year: 2026,
              to_year: 2035,
              rate: "12%",
              fv: 4_500_000,
            },
          ],
        },
      ]),
    );

    expect(screen.getByText("₹25,000/mo")).toBeInTheDocument();
    expect(screen.getByText("2026")).toBeInTheDocument();
    expect(screen.getByText("12%")).toBeInTheDocument();

    expect(screen.getByText("SSY").closest("table")).toBeNull();
    const table = container.querySelector("table");
    expect(table).toBeTruthy();
    expect(within(table!).getByText("From")).toBeInTheDocument();
    expect(within(table!).getByText("Rate")).toBeInTheDocument();
    expect(within(table!).queryByText("SSY")).not.toBeInTheDocument();

    const ssyCard = screen.getByText("SSY").closest("div.rounded-lg");
    expect(table!.compareDocumentPosition(ssyCard!)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
  });
});
