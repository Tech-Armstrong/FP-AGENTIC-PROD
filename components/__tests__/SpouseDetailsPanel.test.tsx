/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SpouseDetailsPanel } from "@/components/SpouseDetailsPanel";

describe("SpouseDetailsPanel", () => {
  const onSpouseSaved = vi.fn();

  beforeEach(() => {
    onSpouseSaved.mockReset();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          record_id: "rec1",
          client_data: {
            client_data: { spouse_name: "Jane Doe" },
          },
        }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders editable inputs for all spouse sections", () => {
    render(
      <SpouseDetailsPanel
        recordId="rec1"
        spouse={{ spouse_name: "John", spouse_dob: "1985-05-01" }}
        onSpouseSaved={onSpouseSaved}
      />,
    );

    expect(screen.getByDisplayValue("John")).toBeInTheDocument();
    expect(screen.getByDisplayValue("1985-05-01")).toBeInTheDocument();
    expect(screen.getAllByRole("spinbutton").length).toBeGreaterThan(0);
    expect(screen.getAllByRole("textbox").length).toBeGreaterThan(0);
  });

  it("PATCHes spouse_name on blur when value changed", async () => {
    render(
      <SpouseDetailsPanel
        recordId="rec1"
        spouse={{ spouse_name: "John" }}
        onSpouseSaved={onSpouseSaved}
      />,
    );

    const nameInput = screen.getByDisplayValue("John");
    fireEvent.change(nameInput, { target: { value: "Jane Doe" } });
    fireEvent.blur(nameInput);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        "/api/airtable/clients/rec1",
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ fields: { spouse_name: "Jane Doe" } }),
        }),
      );
    });
    expect(onSpouseSaved).toHaveBeenCalled();
  });

  it("shows error when PATCH fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        json: async () => ({ error: "Airtable unavailable" }),
      }),
    );

    render(
      <SpouseDetailsPanel
        recordId="rec1"
        spouse={{ spouse_name: "John" }}
        onSpouseSaved={onSpouseSaved}
      />,
    );

    const nameInput = screen.getByDisplayValue("John");
    fireEvent.change(nameInput, { target: { value: "Jane Doe" } });
    fireEvent.blur(nameInput);

    expect(await screen.findByText("Airtable unavailable")).toBeInTheDocument();
    expect(onSpouseSaved).not.toHaveBeenCalled();
  });
});
