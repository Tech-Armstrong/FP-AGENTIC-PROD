/** PDF-only chat policy upload validation (before OCR call). */

export const MAX_POLICY_BYTES = 10 * 1024 * 1024;

export class PolicyUploadValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PolicyUploadValidationError";
  }
}

export function validatePolicyPdf(file: Pick<File, "name" | "type" | "size">): void {
  if (file.size > MAX_POLICY_BYTES) {
    throw new PolicyUploadValidationError(
      `File is too large. Maximum size is ${MAX_POLICY_BYTES / (1024 * 1024)} MB.`,
    );
  }
  const name = (file.name || "").toLowerCase();
  const type = (file.type || "").toLowerCase();
  const isPdf = name.endsWith(".pdf") || type.includes("pdf");
  if (!isPdf) {
    throw new PolicyUploadValidationError(
      "Only PDF policy documents are supported. Please upload a PDF.",
    );
  }
}
