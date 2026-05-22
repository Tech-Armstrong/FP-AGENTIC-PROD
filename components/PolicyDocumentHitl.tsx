"use client";

/**
 * Human-in-the-loop: request_policy_document
 *
 * Uses useCopilotAction + renderAndWaitForResponse (same stack as CopilotSidebar /
 * @copilotkit/react-core v1). Tool name must match Python @tool("request_policy_document").
 *
 * Respond payload contract (JSON):
 *   { uploaded: true, filename, fileType, fileData, extractedText? }
 *   { uploaded: false }
 */

import {
  useCopilotAction,
  useCopilotContext,
  useCopilotReadable,
} from "@copilotkit/react-core";
import { useCallback, useState } from "react";
import {
  UploadPolicyDocument,
  type PolicyUploadRespondPayload,
} from "./UploadPolicyDocument";

export type PolicyDocumentReadable = {
  generated: boolean;
  document_type?: string;
  filename?: string;
  char_count?: number;
  excerpt?: string;
};

function isExecutingStatus(status: string): boolean {
  const s = String(status).toLowerCase();
  return s === "executing" || s === "inprogress";
}

export function PolicyDocumentHitl() {
  const [readable, setReadable] = useState<PolicyDocumentReadable>({
    generated: false,
  });
  const { threadId } = useCopilotContext();
  const effectiveThreadId = threadId || "default";

  useCopilotReadable({
    description:
      "Uploaded insurance/ULIP policy document text for this chat thread (if any).",
    value: readable,
  });

  const onUploadComplete = useCallback((payload: PolicyUploadRespondPayload) => {
    if (payload.uploaded && "extractedText" in payload && payload.extractedText) {
      const text = payload.extractedText;
      setReadable({
        generated: true,
        filename: payload.filename,
        char_count: text.length,
        excerpt: text.slice(0, 2000),
      });
    } else {
      setReadable({ generated: false });
    }
  }, []);

  useCopilotAction({
    name: "request_policy_document",
    description:
      "Ask the user to upload their insurance policy or ULIP document before answering " +
      "policy-specific questions. Call when the user asks about insurance/ULIP and no " +
      "document is in the thread yet.",
    parameters: [
      {
        name: "document_type",
        type: "string",
        description: 'Either "insurance_policy" or "ulip".',
        required: true,
      },
      {
        name: "reason",
        type: "string",
        description: "Short explanation shown on the upload card.",
        required: true,
      },
    ],
    renderAndWaitForResponse: ({ args, status, respond }) => {
      const documentType =
        args.document_type === "ulip" ? "ulip" : "insurance_policy";
      const reason =
        typeof args.reason === "string" && args.reason.trim()
          ? args.reason
          : "Upload your policy document so I can answer from the actual terms.";

      return (
        <UploadPolicyDocument
          documentType={documentType}
          reason={reason}
          status={status}
          executing={isExecutingStatus(status)}
          threadId={effectiveThreadId}
          respond={
            respond
              ? async (payload) => {
                  onUploadComplete(payload);
                  await respond(payload);
                }
              : undefined
          }
        />
      );
    },
  });

  return null;
}
