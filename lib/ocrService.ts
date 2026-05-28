/**
 * Server-side client for the local OCR policy microservice (POST /extract).
 * Must only be called from Next.js route handlers — not from the browser.
 */

export class OCRServiceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "OCRServiceError";
  }
}

export type ExtractedPolicy = Record<string, unknown>;

function ocrBaseUrl(): string {
  const url = process.env.OCR_SERVICE_URL?.trim();
  if (!url) {
    throw new OCRServiceError("OCR_SERVICE_URL is not set");
  }
  return url.replace(/\/$/, "");
}

function ocrTimeoutMs(): number {
  const raw = process.env.OCR_SERVICE_TIMEOUT;
  const n = raw ? Number.parseInt(raw, 10) : 120_000;
  return Number.isFinite(n) && n > 0 ? n : 120_000;
}

/**
 * Send a PDF to the OCR microservice and return ExtractedPolicy JSON.
 */
export async function summarizeDocument(
  fileBytes: ArrayBuffer | Buffer | Uint8Array,
  filename: string,
  mimeType = "application/pdf",
): Promise<ExtractedPolicy> {
  const base = ocrBaseUrl();
  const timeoutMs = ocrTimeoutMs();

  const blob =
    fileBytes instanceof ArrayBuffer
      ? new Blob([fileBytes], { type: mimeType })
      : new Blob([fileBytes as BlobPart], { type: mimeType });

  const form = new FormData();
  form.append("file", blob, filename);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${base}/extract`, {
      method: "POST",
      body: form,
      signal: controller.signal,
    });

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const errBody = (await res.json()) as { detail?: string; error?: string };
        detail = errBody.detail || errBody.error || detail;
      } catch {
        /* ignore */
      }
      throw new OCRServiceError(`OCR service returned ${res.status}: ${detail}`);
    }

    let data: unknown;
    try {
      data = await res.json();
    } catch {
      throw new OCRServiceError("OCR service returned invalid JSON");
    }

    if (!data || typeof data !== "object" || Array.isArray(data)) {
      throw new OCRServiceError("OCR service returned unexpected response shape");
    }

    return data as ExtractedPolicy;
  } catch (err) {
    if (err instanceof OCRServiceError) throw err;
    if (err instanceof Error && err.name === "AbortError") {
      throw new OCRServiceError(`OCR service timed out after ${timeoutMs}ms`);
    }
    throw new OCRServiceError(
      err instanceof Error ? err.message : "OCR service request failed",
    );
  } finally {
    clearTimeout(timer);
  }
}
