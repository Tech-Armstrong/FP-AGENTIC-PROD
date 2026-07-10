/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, within, fireEvent, waitFor } from "@testing-library/react";
import { EducationPlanningSection } from "@/components/EducationPlanningSection";
import type { EducationChildBlock } from "@/lib/educationPlanningView";

const noop = () => {};

const UG_START = 2010 + 18;

const withPgPrePlan: EducationChildBlock = {
  name: "Asha",
  age: 16,
  airtableSlot: 2,
  hasPg: true,
  ug: {
    stream: "MBBS",
    destination: "Domestic",
    duration: 5,
    targetYear: UG_START + 5,
    startYear: UG_START,
    endYear: UG_START + 5,
    currentCost: null,
    futureCost: null,
    corpusGap: null,
    status: null,
  },
  pg: {
    stream: "MD",
    destination: "Domestic",
    duration: 3,
    targetYear: UG_START + 5,
    startYear: UG_START + 5,
    endYear: UG_START + 8,
    currentCost: null,
    futureCost: null,
    corpusGap: null,
    status: null,
  },
};

const naOnly: EducationChildBlock = {
  name: "Ravi",
  age: 14,
  airtableSlot: 1,
  hasPg: false,
  ug: {
    stream: "B.Tech",
    destination: "Domestic",
    duration: 4,
    targetYear: 2012 + 18 + 4,
    startYear: 2012 + 18,
    endYear: 2012 + 18 + 4,
    currentCost: null,
    futureCost: null,
    corpusGap: null,
    status: null,
  },
  pg: null,
};

const baseProps = {
  recordId: "rec1",
  onEducationSaved: noop,
};

const EXPECTED_HEADERS = [
  "Stream",
  "Destination",
  "Course Duration",
  "Start Year",
  "End Year",
  "Target Amount",
];
const REMOVED_HEADERS = ["Current Cost", "Future Cost", "Funding Status", "Particulars", "Target Year"];

function tableCellCounts(table: HTMLTableElement) {
  const headers = within(table).getAllByRole("columnheader");
  const cells = within(table).getAllByRole("cell");
  return { headers: headers.length, cells: cells.length };
}

describe("EducationPlanningSection", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          record_id: "rec1",
          client_data: { education_planning: [] },
        }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("UG table has 6 columns including Destination", () => {
    render(
      <EducationPlanningSection
        {...baseProps}
        blocks={[withPgPrePlan]}
        targets={{}}
        onTargetChange={noop}
      />,
    );
    const ugSection = document.querySelector(".ug-section")!;
    const table = ugSection.querySelector("table") as HTMLTableElement;
    const { headers, cells } = tableCellCounts(table);
    expect(headers).toBe(6);
    expect(cells).toBe(6);
    for (const h of EXPECTED_HEADERS) {
      expect(within(table).getByRole("columnheader", { name: h })).toBeInTheDocument();
    }
    for (const h of REMOVED_HEADERS) {
      expect(within(table).queryByRole("columnheader", { name: h })).not.toBeInTheDocument();
    }
    expect(within(table).getByText("5 yrs")).toBeInTheDocument();
    expect(within(table).getByText(String(UG_START))).toBeInTheDocument();
    expect(within(table).getByText(String(UG_START + 5))).toBeInTheDocument();
  });

  it("child with PG: PG table shows start and end years", () => {
    render(
      <EducationPlanningSection
        {...baseProps}
        blocks={[withPgPrePlan]}
        targets={{}}
        onTargetChange={noop}
      />,
    );
    const pgSection = document.querySelector(".pg-section")!;
    const table = pgSection.querySelector("table") as HTMLTableElement;
    const { headers, cells } = tableCellCounts(table);
    expect(headers).toBe(6);
    expect(cells).toBe(6);
    expect(within(table).getByRole("columnheader", { name: "Target Amount" })).toBeInTheDocument();
    expect(within(table).getByText("3 yrs")).toBeInTheDocument();
    expect(within(table).getByText(String(UG_START + 5))).toBeInTheDocument();
    expect(within(table).getByText(String(UG_START + 8))).toBeInTheDocument();
  });

  it("NA child: PG table absent, note present", () => {
    render(
      <EducationPlanningSection
        {...baseProps}
        blocks={[naOnly]}
        targets={{}}
        onTargetChange={noop}
      />,
    );
    expect(document.querySelector(".pg-section")).toBeNull();
    expect(
      screen.getByText(/No postgraduate education planned for Ravi/),
    ).toBeInTheDocument();
  });

  it("Target Amount renders editable inputs bound to targets", () => {
    const onTargetChange = vi.fn();
    render(
      <EducationPlanningSection
        {...baseProps}
        blocks={[withPgPrePlan]}
        targets={{ Asha: { ug: "5000000", pg: "8000000" } }}
        onTargetChange={onTargetChange}
      />,
    );
    const ugTable = document.querySelector(".ug-section table") as HTMLTableElement;
    const pgTable = document.querySelector(".pg-section table") as HTMLTableElement;
    const ugInput = within(ugTable).getByPlaceholderText("Enter amount") as HTMLInputElement;
    const pgInput = within(pgTable).getByPlaceholderText("Enter amount") as HTMLInputElement;
    expect(ugInput.value).toBe("5000000");
    expect(pgInput.value).toBe("8000000");
    fireEvent.change(ugInput, { target: { value: "6000000" } });
    expect(onTargetChange).toHaveBeenCalledWith("Asha", "ug", "6000000");
  });

  it("changing destination PATCHes the correct Airtable field", async () => {
    const onEducationSaved = vi.fn();
    render(
      <EducationPlanningSection
        recordId="rec1"
        onEducationSaved={onEducationSaved}
        blocks={[withPgPrePlan]}
        targets={{}}
        onTargetChange={noop}
      />,
    );

    const ugTable = document.querySelector(".ug-section table") as HTMLTableElement;
    const select = within(ugTable).getByRole("combobox") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "International" } });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/airtable/clients/rec1",
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({
            fields: { child_2_graduation_destination: "International" },
          }),
        }),
      );
    });
    expect(onEducationSaved).toHaveBeenCalled();
  });

  it("shows error when destination PATCH fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        json: async () => ({ error: "Airtable unavailable" }),
      }),
    );

    render(
      <EducationPlanningSection
        recordId="rec1"
        onEducationSaved={noop}
        blocks={[withPgPrePlan]}
        targets={{}}
        onTargetChange={noop}
      />,
    );

    const ugTable = document.querySelector(".ug-section table") as HTMLTableElement;
    const select = within(ugTable).getByRole("combobox") as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "International" } });

    expect(await screen.findByText("Airtable unavailable")).toBeInTheDocument();
  });

  it("NA child: no PG target input", () => {
    render(
      <EducationPlanningSection
        {...baseProps}
        blocks={[naOnly]}
        targets={{}}
        onTargetChange={noop}
      />,
    );
    expect(document.querySelectorAll('input[placeholder="Enter amount"]')).toHaveLength(1);
  });

  it("MBBS shows 5 yrs in UG table; Other shows Airtable duration", () => {
    render(
      <EducationPlanningSection
        {...baseProps}
        blocks={[withPgPrePlan]}
        targets={{}}
        onTargetChange={noop}
      />,
    );
    expect(screen.getByText("5 yrs")).toBeInTheDocument();

    const otherChild: EducationChildBlock = {
      name: "Sam",
      age: 10,
      airtableSlot: 3,
      hasPg: false,
      ug: {
        stream: "Other",
        destination: "Domestic",
        duration: 6,
        targetYear: 2015 + 18 + 6,
        startYear: 2015 + 18,
        endYear: 2015 + 18 + 6,
        currentCost: null,
        futureCost: null,
        corpusGap: null,
        status: null,
      },
      pg: null,
    };
    render(
      <EducationPlanningSection
        {...baseProps}
        blocks={[otherChild]}
        targets={{}}
        onTargetChange={noop}
      />,
    );
    expect(screen.getByText("6 yrs")).toBeInTheDocument();
  });

  it("renders separate blocks for multiple children", () => {
    render(
      <EducationPlanningSection
        {...baseProps}
        blocks={[withPgPrePlan, naOnly]}
        targets={{}}
        onTargetChange={noop}
      />,
    );
    expect(document.querySelectorAll(".child-education-block")).toHaveLength(2);
  });
});
