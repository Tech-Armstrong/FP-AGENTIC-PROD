/**
 * @vitest-environment jsdom
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SsyTrackerSection } from "../SsyTrackerSection";

describe("SsyTrackerSection", () => {
  it("renders child SSY metrics and locked badge", () => {
    render(
      <SsyTrackerSection
        rows={[
          {
            child_name: "Ananya",
            total_fv: 500000,
            total_withdrawn: 150000,
            remaining_balance: 350000,
            maturity_year: 2037,
            locked: true,
          },
        ]}
      />,
    );
    expect(screen.getByText("SSY Tracker")).toBeTruthy();
    expect(screen.getByText("Ananya")).toBeTruthy();
    expect(screen.getByText(/Locked until 2037/)).toBeTruthy();
    expect(screen.getByText("₹5,00,000")).toBeTruthy();
    expect(screen.getByText("₹1,50,000")).toBeTruthy();
    expect(screen.getByText("₹3,50,000")).toBeTruthy();
  });

  it("returns null when rows empty", () => {
    const { container } = render(<SsyTrackerSection rows={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
