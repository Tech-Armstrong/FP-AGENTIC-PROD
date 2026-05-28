import { NextResponse } from "next/server";
import { OCRServiceError, summarizeDocument } from "@/lib/ocrService";
import { PolicyUploadValidationError, validatePolicyPdf } from "@/lib/validatePolicyUpload";

export async function POST(req: Request) {
  const contentType = req.headers.get("content-type") || "";

  if (!contentType.includes("multipart/form-data")) {
    return NextResponse.json(
      { detail: "Expected multipart/form-data with a PDF file field named 'file'" },
      { status: 400 },
    );
  }

  let form: FormData;
  try {
    form = await req.formData();
  } catch {
    return NextResponse.json({ detail: "Invalid multipart body" }, { status: 400 });
  }

  const file = form.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ detail: "Missing file upload" }, { status: 400 });
  }

  try {
    validatePolicyPdf(file);
  } catch (err) {
    if (err instanceof PolicyUploadValidationError) {
      return NextResponse.json({ detail: err.message }, { status: 400 });
    }
    throw err;
  }

  try {
    const bytes = await file.arrayBuffer();
    const policySummary = await summarizeDocument(bytes, file.name, file.type || "application/pdf");
    const contextText = JSON.stringify(policySummary);

    return NextResponse.json({
      policy_summary: policySummary,
      char_count: contextText.length,
      filename: file.name,
    });
  } catch (err) {
    if (err instanceof OCRServiceError) {
      return NextResponse.json(
        {
          detail:
            "Couldn't process the document right now. Please retry in a moment.",
          error: err.message,
        },
        { status: 502 },
      );
    }
    return NextResponse.json(
      { detail: "Unexpected error processing document" },
      { status: 500 },
    );
  }
}
