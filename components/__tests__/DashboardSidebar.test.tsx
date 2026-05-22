/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DashboardSidebar } from "../DashboardSidebar";

const clients = [
  { record_id: "rec1", name: "Jane Doe" },
  { record_id: "rec2", name: "John Smith" },
  { record_id: "rec3", name: "Alice Wonder" },
];

describe("DashboardSidebar", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders Clients heading and search input when expanded", async () => {
    render(
      <DashboardSidebar
        clients={clients}
        selectedId={null}
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    await screen.findByRole("complementary", { name: /clients sidebar/i });
    expect(screen.getByRole("heading", { name: "Clients" })).toBeTruthy();
    expect(screen.getByRole("searchbox", { name: /search clients/i })).toBeTruthy();
    expect(screen.queryByAltText("Armstrong Capital")).toBeNull();
  });

  it("filters client list as user types", async () => {
    render(
      <DashboardSidebar
        clients={clients}
        selectedId={null}
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    await screen.findByRole("searchbox", { name: /search clients/i });
    fireEvent.change(screen.getByRole("searchbox", { name: /search clients/i }), {
      target: { value: "jane" },
    });
    expect(screen.getByRole("button", { name: /Jane Doe/i })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /John Smith/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /Alice Wonder/i })).toBeNull();
  });

  it("filters by record id", async () => {
    render(
      <DashboardSidebar
        clients={clients}
        selectedId={null}
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    const search = await screen.findByRole("searchbox", { name: /search clients/i });
    fireEvent.change(search, { target: { value: "rec2" } });
    expect(screen.getByRole("button", { name: /John Smith/i })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Jane Doe/i })).toBeNull();
  });

  it("clears search and restores full list", async () => {
    render(
      <DashboardSidebar
        clients={clients}
        selectedId={null}
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    const search = await screen.findByRole("searchbox", { name: /search clients/i });
    fireEvent.change(search, { target: { value: "jane" } });
    expect(screen.queryByRole("button", { name: /John Smith/i })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /clear search/i }));
    expect(screen.getByRole("button", { name: /Jane Doe/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /John Smith/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Alice Wonder/i })).toBeTruthy();
  });

  it("shows empty state when filter matches nothing", async () => {
    render(
      <DashboardSidebar
        clients={clients}
        selectedId={null}
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    const search = await screen.findByRole("searchbox", { name: /search clients/i });
    fireEvent.change(search, { target: { value: "zzznomatch" } });
    expect(screen.getByText("No clients found")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Jane Doe/i })).toBeNull();
  });

  it("toggles between collapsed and expanded on button click", async () => {
    render(
      <DashboardSidebar
        clients={clients}
        selectedId="rec1"
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    const sidebar = await screen.findByRole("complementary", {
      name: /clients sidebar/i,
    });
    expect(sidebar.className).toMatch(/w-64/);
    expect(screen.getByRole("heading", { name: "Clients" })).toBeTruthy();

    fireEvent.click(
      screen.getByRole("button", { name: /collapse sidebar/i }),
    );
    expect(sidebar.className).toMatch(/w-14/);
    expect(screen.queryByRole("heading", { name: "Clients" })).toBeNull();
    expect(screen.queryByRole("searchbox", { name: /search clients/i })).toBeNull();
    expect(localStorage.getItem("dashboard-sidebar-collapsed")).toBe("true");

    fireEvent.click(
      screen.getByRole("button", { name: "Expand sidebar" }),
    );
    expect(sidebar.className).toMatch(/w-64/);
    expect(screen.getByRole("heading", { name: "Clients" })).toBeTruthy();
    expect(localStorage.getItem("dashboard-sidebar-collapsed")).toBe("false");
  });

  it("does not display client record ids in sidebar rows", async () => {
    render(
      <DashboardSidebar
        clients={clients}
        selectedId="rec1"
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    await screen.findByRole("complementary", { name: /clients sidebar/i });
    const jane = screen.getByRole("button", { name: /Jane Doe/i });
    expect(jane.textContent).not.toMatch(/rec1/i);
    expect(screen.getByRole("button", { name: /John Smith/i }).textContent).not.toMatch(
      /rec2/i,
    );
  });

  it("marks selected client with aria-current", async () => {
    render(
      <DashboardSidebar
        clients={clients}
        selectedId="rec1"
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    await screen.findByRole("complementary", { name: /clients sidebar/i });
    const selected = screen.getByRole("button", { name: /Jane Doe/i });
    expect(selected.getAttribute("aria-current")).toBe("true");
    expect(selected.getAttribute("data-selected")).toBe("true");
    expect(screen.getByRole("button", { name: /John Smith/i }).getAttribute("aria-current")).toBeNull();
  });

  it("shows client initials when collapsed", async () => {
    localStorage.setItem("dashboard-sidebar-collapsed", "true");
    render(
      <DashboardSidebar
        clients={clients}
        selectedId="rec1"
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    await screen.findByRole("complementary", { name: /clients sidebar/i });
    expect(screen.getByTitle("Jane Doe")).toBeTruthy();
    expect(screen.getByText("JD")).toBeTruthy();
    expect(screen.getByRole("button", { name: /expand sidebar to search/i })).toBeTruthy();
  });

  it("expands sidebar when search icon is clicked in collapsed rail", async () => {
    localStorage.setItem("dashboard-sidebar-collapsed", "true");
    render(
      <DashboardSidebar
        clients={clients}
        selectedId={null}
        onSelect={vi.fn()}
        loadingList={false}
        error={null}
      />,
    );
    const sidebar = await screen.findByRole("complementary", {
      name: /clients sidebar/i,
    });
    expect(sidebar.className).toMatch(/w-14/);

    fireEvent.click(
      screen.getByRole("button", { name: /expand sidebar to search/i }),
    );
    expect(sidebar.className).toMatch(/w-64/);
    expect(screen.getByRole("searchbox", { name: /search clients/i })).toBeTruthy();
  });
});

describe("CopilotKit branding", () => {
  it("Footer does not render Powered by CopilotKit", async () => {
    const { Footer } = await import("../Footer");
    render(<Footer />);
    expect(screen.queryByText(/Powered by CopilotKit/i)).toBeNull();
  });

  it("globals keep chat input container visible (not .poweredByContainer)", () => {
    render(
      <div className="copilotKitSidebar">
        <div className="copilotKitInputContainer poweredByContainer">
          <div className="copilotKitInput">
            <textarea placeholder="Ask about sales…" aria-label="Chat message" />
          </div>
          <p className="poweredBy" style={{ display: "block" }}>
            Powered by CopilotKit
          </p>
        </div>
      </div>,
    );
    const container = screen
      .getByPlaceholderText("Ask about sales…")
      .closest(".copilotKitInputContainer");
    expect(container).toBeTruthy();
    expect(getComputedStyle(container!).display).not.toBe("none");
    expect(screen.getByRole("textbox", { name: /chat message/i })).toBeTruthy();
  });
});
