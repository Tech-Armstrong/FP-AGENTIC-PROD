import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { summarizeDocument, OCRServiceError } from "@/lib/ocrService";
import { validatePolicyPdf, PolicyUploadValidationError } from "@/lib/validatePolicyUpload";

describe("validatePolicyPdf", () => {
  it("accepts PDF under size limit", () => {
    expect(() =>
      validatePolicyPdf({ name: "policy.pdf", type: "application/pdf", size: 1000 }),
    ).not.toThrow();
  });

  it("rejects non-PDF", () => {
    expect(() =>
      validatePolicyPdf({ name: "notes.txt", type: "text/plain", size: 100 }),
    ).toThrow(PolicyUploadValidationError);
  });

  it("rejects oversized file", () => {
    expect(() =>
      validatePolicyPdf({
        name: "big.pdf",
        type: "application/pdf",
        size: 11 * 1024 * 1024,
      }),
    ).toThrow(/too large/i);
  });
});

describe("summarizeDocument", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.restoreAllMocks();
    process.env = { ...originalEnv, OCR_SERVICE_URL: "http://localhost:8010" };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("returns parsed JSON on success", async () => {
    const summary = { insurer: "ABC", sum_assured: "500000" };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => summary,
      }),
    );

    const out = await summarizeDocument(new TextEncoder().encode("%PDF"), "policy.pdf");
    expect(out).toEqual(summary);

    const fetchMock = vi.mocked(fetch);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8010/extract",
      expect.objectContaining({ method: "POST" }),
    );
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.method).toBe("POST");
    expect(init?.body).toBeInstanceOf(FormData);
  });

  it("throws on timeout (abort)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(Object.assign(new Error("aborted"), { name: "AbortError" })),
    );
    await expect(
      summarizeDocument(new TextEncoder().encode("x"), "p.pdf"),
    ).rejects.toThrow(OCRServiceError);
  });

  it("throws on non-200", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        statusText: "Unavailable",
        json: async () => ({ detail: "down" }),
      }),
    );
    await expect(
      summarizeDocument(new TextEncoder().encode("x"), "p.pdf"),
    ).rejects.toThrow(/503/);
  });

  it("throws when OCR_SERVICE_URL unset", async () => {
    delete process.env.OCR_SERVICE_URL;
    await expect(
      summarizeDocument(new TextEncoder().encode("x"), "p.pdf"),
    ).rejects.toThrow(/OCR_SERVICE_URL/);
  });
});
