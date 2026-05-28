"use client";

import * as React from "react";
import { FileUp, Upload, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { validatePolicyPdf, PolicyUploadValidationError } from "@/lib/validatePolicyUpload";

const ACCEPT = ".pdf";

/** Agreed respond(...) payload — OCR summary only; no raw PDF bytes. */
export type PolicyUploadRespondPayload =
  | {
      uploaded: true;
      filename: string;
      fileType: string;
      policySummary: Record<string, unknown>;
    }
  | { uploaded: false };

type Props = {
  documentType: "insurance_policy" | "ulip";
  reason: string;
  status: string;
  executing: boolean;
  threadId?: string;
  respond?: (result: PolicyUploadRespondPayload) => void | Promise<void>;
};

function labelForType(documentType: string): string {
  return documentType === "ulip" ? "ULIP" : "Insurance Policy";
}

async function summarizeOnServer(
  file: File,
): Promise<{ policy_summary: Record<string, unknown> }> {
  const form = new FormData();
  form.append("file", file, file.name);
  const res = await fetch("/api/parse-policy-document", {
    method: "POST",
    body: form,
  });
  const data = (await res.json()) as {
    policy_summary?: Record<string, unknown>;
    detail?: string;
    error?: string;
  };
  if (!res.ok) {
    throw new Error(
      data.detail ||
        data.error ||
        "Couldn't process the document right now, please retry.",
    );
  }
  if (!data.policy_summary) {
    throw new Error("OCR service returned no policy summary");
  }
  return { policy_summary: data.policy_summary };
}

export function UploadPolicyDocument({
  documentType,
  reason,
  status,
  executing,
  threadId: _threadId = "default",
  respond,
}: Props) {
  const [file, setFile] = React.useState<File | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [outcome, setOutcome] = React.useState<"uploaded" | "skipped" | null>(
    null,
  );
  const [outcomeName, setOutcomeName] = React.useState<string | null>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const canInteract = executing && Boolean(respond);

  const onPick = (picked: File | null) => {
    setError(null);
    if (!picked) {
      setFile(null);
      return;
    }
    try {
      validatePolicyPdf(picked);
      setFile(picked);
    } catch (err) {
      setError(
        err instanceof PolicyUploadValidationError
          ? err.message
          : "Invalid file",
      );
      setFile(null);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (!canInteract) return;
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) onPick(dropped);
  };

  const onUpload = async () => {
    if (!file || !respond || !canInteract) return;
    setBusy(true);
    setError(null);
    try {
      const { policy_summary } = await summarizeOnServer(file);
      await respond({
        uploaded: true,
        filename: file.name,
        fileType: file.type || "application/pdf",
        policySummary: policy_summary,
      });
      setOutcome("uploaded");
      setOutcomeName(file.name);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const onSkip = async () => {
    if (!respond || !canInteract) return;
    await respond({ uploaded: false });
    setOutcome("skipped");
  };

  if (String(status).toLowerCase() === "complete" && outcome === "uploaded") {
    return (
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-100">
        ✓ Uploaded {outcomeName}
      </div>
    );
  }

  if (String(status).toLowerCase() === "complete" && outcome === "skipped") {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
        Skipped — answering without your policy document.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
        Upload your {labelForType(documentType)} document
      </h4>
      <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">{reason}</p>

      <div
        role="button"
        tabIndex={0}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        onClick={() => canInteract && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (canInteract) inputRef.current?.click();
          }
        }}
        className={cn(
          "mt-3 flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors",
          canInteract
            ? "cursor-pointer border-blue-200 bg-blue-50/50 hover:border-blue-400 dark:border-blue-800 dark:bg-blue-950/20"
            : "cursor-not-allowed border-gray-200 bg-gray-50 opacity-60 dark:border-gray-700 dark:bg-gray-900",
        )}
      >
        <FileUp className="mb-2 h-8 w-8 text-blue-500" />
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Drag & drop or click to choose a PDF
        </p>
        <p className="mt-1 text-xs text-gray-500">PDF only · max 10 MB · OCR summarized</p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          disabled={!canInteract}
          onChange={(e) => onPick(e.target.files?.[0] ?? null)}
        />
      </div>

      {file && (
        <div className="mt-2 flex items-center gap-2 rounded-md border border-gray-100 bg-gray-50 px-2 py-1.5 text-xs dark:border-gray-700 dark:bg-gray-900">
          <span className="flex-1 truncate font-medium text-gray-800 dark:text-gray-200">
            {file.name}
          </span>
          <span className="text-gray-500">
            {(file.size / 1024).toFixed(0)} KB
          </span>
          {canInteract && (
            <button
              type="button"
              aria-label="Remove file"
              className="text-gray-400 hover:text-gray-600"
              onClick={(e) => {
                e.stopPropagation();
                onPick(null);
              }}
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      )}

      {error && (
        <p className="mt-2 text-xs text-red-600 dark:text-red-400">{error}</p>
      )}

      <div className="mt-3 flex gap-2">
        <button
          type="button"
          disabled={!canInteract || !file || busy}
          onClick={onUpload}
          className={cn(
            "inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-white",
            canInteract && file && !busy
              ? "bg-blue-600 hover:bg-blue-700"
              : "cursor-not-allowed bg-blue-300 dark:bg-blue-900",
          )}
        >
          <Upload className="h-4 w-4" />
          {busy ? "Processing…" : "Upload"}
        </button>
        <button
          type="button"
          disabled={!canInteract || busy}
          onClick={onSkip}
          className="rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          Skip
        </button>
      </div>
    </div>
  );
}
