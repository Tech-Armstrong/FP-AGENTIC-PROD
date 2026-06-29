/**
 * @vitest-environment jsdom
 *
 * Mounts the full ClientsDashboard with CopilotKit/theme and the heavy child
 * components stubbed, drives client selection through a stubbed sidebar, and
 * asserts the Overview tab renders the Medical Insurance section (mirroring Life
 * Insurance) — with an Employer + Self row — and hides it when there is no data.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

vi.mock("@copilotkit/react-core", () => ({
  useCopilotAction: () => {},
  useCopilotReadable: () => {},
}));

vi.mock("next-themes", () => ({
  useTheme: () => ({ theme: "light", resolvedTheme: "light", setTheme: () => {} }),
}));

vi.mock("../generative-ui/SearchResults", () => ({ SearchResults: () => null }));
vi.mock("../generative-ui/CurrentDateTool", () => ({ CurrentDateTool: () => null }));

vi.mock("../FinancialPlanPanel", () => ({
  FinancialPlanPanel: () => null,
  emptyAppliedRates: () => ({
    epf: null,
    ppf: null,
    nps: null,
    mfExpectedReturn: null,
    rsuGrowth: 0,
  }),
}));

vi.mock("../DashboardSidebar", () => ({
  DashboardSidebar: ({
    clients,
    onSelect,
  }: {
    clients: { record_id: string; name: string }[];
    onSelect: (id: string) => void;
  }) => (
    <div>
      {clients.map((c) => (
        <button key={c.record_id} onClick={() => onSelect(c.record_id)}>
          {c.name}
        </button>
      ))}
    </div>
  ),
}));

vi.mock("../SpouseDetailsPanel", () => ({
  SpouseDetailsPanel: () => null,
  mergeSpouseData: () => null,
}));

vi.mock("../RealEstateTable", () => ({ RealEstateTable: () => null }));
vi.mock("../MarriageGoalsSection", () => ({ MarriageGoalsSection: () => null }));
vi.mock("../EducationPlanningSection", () => ({ EducationPlanningSection: () => null }));

import { ClientsDashboard } from "../ClientsDashboard";

type MedicalRow = {
  policy_type: string;
  company_name: string;
  coverage_value: number;
};

function makeDetail(medical: MedicalRow[]) {
  return {
    record_id: "rec1",
    client_data: {
      client_data: {
        name: "Jane Doe",
        pan: "",
        organization_name: "",
        date_of_birth: "1980-01-01",
        retirement_age: 60,
        spouse_name: "",
        spouse_dob: "",
        if_any_kids: false,
        children: [],
      },
      investment_details: {
        financial_summary: [],
        real_estate_investment: [],
        retirement_investments: { epf: [], ppf: [], nps: [], ulip: [] },
        bonds: [],
        mutual_funds: [],
        direct_equity: [],
        reits: [],
        pms_aif: [],
        esops: [],
        rsu: [],
        fixed_deposits: [],
        ulips: [],
        lic_policies: [],
      },
      financial_goals: [],
      liabilities: [],
      education_planning: [],
      life_insurance: [],
      medical_insurance: medical,
    },
  };
}

function makeFetch(detail: unknown) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/airtable/clients/")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(detail),
      } as Response);
    }
    if (url.endsWith("/api/airtable/clients")) {
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({ clients: [{ record_id: "rec1", name: "Jane Doe" }] }),
      } as Response);
    }
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({}),
    } as Response);
  });
}

describe("ClientsDashboard medical insurance (Overview tab)", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    );
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        unobserve() {}
        disconnect() {}
      },
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders Employer and Self medical policies in the Overview", async () => {
    vi.stubGlobal(
      "fetch",
      makeFetch(
        makeDetail([
          { policy_type: "Employer", company_name: "Star Health", coverage_value: 500000 },
          { policy_type: "Self", company_name: "HDFC Ergo", coverage_value: 1000000 },
        ]),
      ),
    );

    render(<ClientsDashboard />);
    fireEvent.click(await screen.findByRole("button", { name: "Jane Doe" }));

    await screen.findByText("Medical Insurance");
    expect(screen.getByText("Star Health")).toBeTruthy();
    expect(screen.getByText("HDFC Ergo")).toBeTruthy();
    expect(screen.getByText("Employer")).toBeTruthy();
    expect(screen.getByText("Self")).toBeTruthy();
    // Coverage is formatted via the dashboard's inr() helper.
    expect(screen.getByText("₹5.00L")).toBeTruthy();
    expect(screen.getByText("₹10.00L")).toBeTruthy();
  });

  it("hides the Medical Insurance section when there are no policies", async () => {
    vi.stubGlobal("fetch", makeFetch(makeDetail([])));

    render(<ClientsDashboard />);
    fireEvent.click(await screen.findByRole("button", { name: "Jane Doe" }));

    // Anchor: an Overview stat that is always present once the detail loads.
    await screen.findByText("Total Investments");
    expect(screen.queryByText("Medical Insurance")).toBeNull();
  });
});
