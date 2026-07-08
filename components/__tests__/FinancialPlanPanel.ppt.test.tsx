/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import {
  FinancialPlanPanel,
  emptyAppliedRates,
  type PlanTab,
  type PlanSummary,
} from "../FinancialPlanPanel";
import type { PlanInputSnapshot } from "@/lib/planInputValidation";

const baseSummary: PlanSummary = {
  client_name: "Test Client",
  spending_behavior: { saving_ratio: 0.25, expense_ratio: 0.75, red_flag: false },
  liquidity_flag: "OK",
  flexibility: "Medium",
};

const baseSnapshot: PlanInputSnapshot = {
  rates: { epf: "", ppf: "", nps: "", mf: "", rsu: "" },
  educationTargets: {},
  desiredMonthlyAnnuity: "",
  retirementAge: "60",
};

function renderPanel(planTabs: PlanTab[]) {
  const activeId = planTabs[0]?.id ?? null;
  return render(
    <FinancialPlanPanel
      recordId="rec123"
      planOverrides={null}
      originalRates={emptyAppliedRates()}
      planTabs={planTabs}
      activeTabId={activeId}
      onActiveTabChange={() => {}}
      onPlanComplete={() => {}}
      desiredMonthlyAnnuity=""
      onDesiredMonthlyAnnuityChange={() => {}}
      retirementAge="60"
      onRetirementAgeChange={() => {}}
      makePlanBlockReason={null}
      currentInputSnapshot={baseSnapshot}
    />,
  );
}

describe("FinancialPlanPanel PPT download", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        blob: async () => new Blob(["PK"], { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" }),
        headers: {
          get: (name: string) =>
            name.toLowerCase() === "content-disposition"
              ? 'attachment; filename="Test_Client_financial_plan.pptx"'
              : null,
        },
      }),
    );
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:mock"),
      revokeObjectURL: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows Download PPT when active tab has workflowState", () => {
    renderPanel([
      {
        id: "plan-1",
        label: "Original",
        overrides: null,
        appliedRates: emptyAppliedRates(),
        inputSnapshot: baseSnapshot,
        summary: baseSummary,
        workflowState: { client_data: { client_data: { name: "Test" } } },
      },
    ]);
    expect(screen.getByRole("button", { name: /Download PPT/i })).toBeTruthy();
  });

  it("hides Download PPT when workflowState is missing", () => {
    renderPanel([
      {
        id: "plan-1",
        label: "Original",
        overrides: null,
        appliedRates: emptyAppliedRates(),
        inputSnapshot: baseSnapshot,
        summary: baseSummary,
      },
    ]);
    expect(screen.queryByRole("button", { name: /Download PPT/i })).toBeNull();
  });

  it("calls /api/financial-plan/ppt on button click", async () => {
    const workflowState = { client_data: { client_data: { name: "Test" } } };
    renderPanel([
      {
        id: "plan-1",
        label: "Original",
        overrides: null,
        appliedRates: emptyAppliedRates(),
        inputSnapshot: baseSnapshot,
        summary: baseSummary,
        workflowState,
      },
    ]);

    fireEvent.click(screen.getByRole("button", { name: /Download PPT/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/financial-plan/ppt",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ workflow_state: workflowState }),
        }),
      );
    });
  });
});
