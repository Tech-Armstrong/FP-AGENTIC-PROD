/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { UploadPolicyDocument } from "../UploadPolicyDocument";

describe("UploadPolicyDocument", () => {
  const respond = vi.fn();

  beforeEach(() => {
    respond.mockReset();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ extracted_text: "Parsed policy text" }),
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

  it("enables Upload after file selection and calls respond with agreed shape", async () => {
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
    expect(typeof payload.fileData).toBe("string");
    expect(payload.extractedText).toBe("Parsed policy text");
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
