/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { UploadPolicyDocument } from "../UploadPolicyDocument";

const MOCK_SUMMARY = {
  insurer: "Test Life",
  sum_assured: "1000000",
};

describe("UploadPolicyDocument", () => {
  const respond = vi.fn();

  beforeEach(() => {
    respond.mockReset();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ policy_summary: MOCK_SUMMARY }),
      }),
    );
  });

  it("renders document type and reason", () => {
    render(
      <UploadPolicyDocument
        documentType="ulip"
        reason="Need your ULIP document"
        status="executing"
        executing
        respond={respond}
      />,
    );
    expect(screen.getByText(/Upload your ULIP document/i)).toBeTruthy();
    expect(screen.getByText("Need your ULIP document")).toBeTruthy();
  });

  it("calls respond with OCR summary only — no raw PDF base64", async () => {
    render(
      <UploadPolicyDocument
        documentType="insurance_policy"
        reason="Upload please"
        status="executing"
        executing
        threadId="test-thread"
        respond={respond}
      />,
    );
    const file = new File(["%PDF"], "policy.pdf", { type: "application/pdf" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: /Upload/i }));
    await waitFor(() => expect(respond).toHaveBeenCalled());
    const payload = respond.mock.calls[0][0];
    expect(payload.uploaded).toBe(true);
    expect(payload.filename).toBe("policy.pdf");
    expect(payload.fileType).toBe("application/pdf");
    expect(payload.policySummary).toEqual(MOCK_SUMMARY);
    expect(payload).not.toHaveProperty("fileData");
    expect(payload).not.toHaveProperty("extractedText");

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/parse-policy-document",
      expect.objectContaining({ method: "POST" }),
    );
    const body = fetchMock.mock.calls[0][1]?.body;
    expect(body).toBeInstanceOf(FormData);
  });

  it("shows OCR error without falling back to raw PDF", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          detail: "Couldn't process the document right now. Please retry in a moment.",
        }),
      }),
    );
    render(
      <UploadPolicyDocument
        documentType="insurance_policy"
        reason="Upload please"
        status="executing"
        executing
        respond={respond}
      />,
    );
    const file = new File(["%PDF"], "policy.pdf", { type: "application/pdf" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: /Upload/i }));
    await waitFor(() =>
      expect(screen.getByText(/Couldn't process the document/i)).toBeTruthy(),
    );
    expect(respond).not.toHaveBeenCalled();
  });

  it("Skip calls respond with uploaded false", async () => {
    render(
      <UploadPolicyDocument
        documentType="insurance_policy"
        reason="Upload please"
        status="executing"
        executing
        respond={respond}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Skip/i }));
    await waitFor(() => expect(respond).toHaveBeenCalledWith({ uploaded: false }));
  });

  it("rejects oversized file without calling respond", async () => {
    render(
      <UploadPolicyDocument
        documentType="insurance_policy"
        reason="Upload please"
        status="executing"
        executing
        respond={respond}
      />,
    );
    const big = new File([new ArrayBuffer(11 * 1024 * 1024)], "big.pdf", {
      type: "application/pdf",
    });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [big] } });
    expect(screen.getByText(/File is too large/i)).toBeTruthy();
    expect(respond).not.toHaveBeenCalled();
  });

  it("rejects non-PDF file", async () => {
    render(
      <UploadPolicyDocument
        documentType="insurance_policy"
        reason="Upload please"
        status="executing"
        executing
        respond={respond}
      />,
    );
    const txt = new File(["hello"], "notes.txt", { type: "text/plain" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [txt] } });
    expect(screen.getByText(/Only PDF/i)).toBeTruthy();
  });

  it("disables actions when not executing", () => {
    render(
      <UploadPolicyDocument
        documentType="insurance_policy"
        reason="Upload please"
        status="inProgress"
        executing={false}
        respond={respond}
      />,
    );
    expect(screen.getByRole("button", { name: /Upload/i })).toHaveProperty(
      "disabled",
      true,
    );
  });
});
