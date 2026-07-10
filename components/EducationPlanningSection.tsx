"use client";

import { useCallback, useEffect, useState } from "react";
import type { EducationChildBlock, EducationStageView } from "@/lib/educationPlanningView";
import {
  destinationSelectValue,
  EDUCATION_DESTINATION_OPTIONS,
  educationDestinationAirtableKey,
  normalizeEducationDestination,
} from "@/lib/educationAirtableFields";

const TH =
  "align-middle px-4 py-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400";
const TD = "align-middle px-4 py-2 text-gray-700 dark:text-gray-300";
const SELECT =
  "w-full rounded border border-gray-300 bg-white px-2 py-1 text-center text-sm text-gray-900 focus:border-brand focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100";

type FieldStatus = "idle" | "saving" | "saved" | "error";
type DestinationFieldKey = `${string}:ug` | `${string}:pg`;

function fmtYear(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return String(n);
}

function statusText(status: FieldStatus, error?: string): string | null {
  if (status === "saving") return "Saving…";
  if (status === "saved") return "Saved";
  if (status === "error") return error ?? "Save failed";
  return null;
}

function statusBorder(status: FieldStatus): string {
  if (status === "error") return "border-red-400 dark:border-red-500";
  if (status === "saved") return "border-green-400 dark:border-green-500";
  if (status === "saving") return "border-blue-300 dark:border-blue-500";
  return "";
}

function destinationFieldKey(childName: string, side: "ug" | "pg"): DestinationFieldKey {
  return `${childName}:${side}`;
}

/** Target Amount = user-entered final corpus (no inflation). */
function StageTable({
  stage,
  value,
  onChange,
  destinationValue,
  onDestinationChange,
  destinationStatus,
  destinationError,
  destinationDisabled,
}: {
  stage: EducationStageView;
  value: string;
  onChange: (v: string) => void;
  destinationValue: string;
  onDestinationChange: (v: string) => void;
  destinationStatus: FieldStatus;
  destinationError?: string;
  destinationDisabled?: boolean;
}) {
  const hint = statusText(destinationStatus, destinationError);

  return (
    <table className="w-full border-collapse text-xs">
      <thead>
        <tr className="border-b border-gray-100 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
          <th className={`${TH} text-left`}>Stream</th>
          <th className={`${TH} text-center`}>Destination</th>
          <th className={`${TH} text-center`}>Course Duration</th>
          <th className={`${TH} text-center`}>Start Year</th>
          <th className={`${TH} text-center`}>End Year</th>
          <th className={`${TH} text-right`}>Target Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr className="border-b border-gray-100 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800/50">
          <td className={`${TD} text-left text-gray-900 dark:text-gray-100`}>
            {stage.stream ?? "—"}
          </td>
          <td className={`${TD} text-center`}>
            <select
              value={destinationValue}
              disabled={destinationDisabled || destinationStatus === "saving"}
              onChange={(e) => onDestinationChange(e.target.value)}
              className={`${SELECT} ${statusBorder(destinationStatus)}`}
            >
              <option value="">Select…</option>
              {EDUCATION_DESTINATION_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {hint ? (
              <p
                className={`mt-1 text-[10px] ${
                  destinationStatus === "error"
                    ? "text-red-500"
                    : destinationStatus === "saved"
                      ? "text-green-600 dark:text-green-400"
                      : "text-gray-400"
                }`}
              >
                {hint}
              </p>
            ) : null}
          </td>
          <td className={`${TD} text-center`}>
            {stage.duration != null ? `${stage.duration} yrs` : "—"}
          </td>
          <td className={`${TD} text-center`}>{fmtYear(stage.startYear)}</td>
          <td className={`${TD} text-center`}>{fmtYear(stage.endYear)}</td>
          <td className={`${TD} text-right`}>
            <input
              type="number"
              min="0"
              inputMode="numeric"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder="Enter amount"
              className="w-32 rounded border border-gray-300 bg-white px-2 py-1 text-right text-sm
                         text-gray-900 focus:border-brand focus:outline-none
                         dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            />
          </td>
        </tr>
      </tbody>
    </table>
  );
}

export function EducationPlanningSection({
  recordId,
  blocks,
  targets,
  onTargetChange,
  onEducationSaved,
  disabled = false,
}: {
  recordId: string;
  blocks: EducationChildBlock[];
  targets: Record<string, { ug?: string; pg?: string }>;
  onTargetChange: (childName: string, side: "ug" | "pg", value: string) => void;
  onEducationSaved: (clientData: Record<string, unknown>) => void;
  disabled?: boolean;
}) {
  const [destinationDraft, setDestinationDraft] = useState<Record<DestinationFieldKey, string>>(
    {},
  );
  const [destinationBaseline, setDestinationBaseline] = useState<
    Record<DestinationFieldKey, string>
  >({});
  const [fieldStatus, setFieldStatus] = useState<Partial<Record<DestinationFieldKey, FieldStatus>>>(
    {},
  );
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<DestinationFieldKey, string>>>({});

  useEffect(() => {
    const nextDraft = {} as Record<DestinationFieldKey, string>;
    const nextBaseline = {} as Record<DestinationFieldKey, string>;
    for (const child of blocks) {
      const ugKey = destinationFieldKey(child.name, "ug");
      const ugValue = destinationSelectValue(child.ug.destination);
      nextDraft[ugKey] = ugValue;
      nextBaseline[ugKey] = ugValue;
      if (child.hasPg && child.pg) {
        const pgKey = destinationFieldKey(child.name, "pg");
        const pgValue = destinationSelectValue(child.pg.destination);
        nextDraft[pgKey] = pgValue;
        nextBaseline[pgKey] = pgValue;
      }
    }
    setDestinationDraft(nextDraft);
    setDestinationBaseline(nextBaseline);
    setFieldStatus({});
    setFieldErrors({});
    // Reset only when switching clients or refreshed education blocks.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordId]);

  const saveDestination = useCallback(
    async (child: EducationChildBlock, side: "ug" | "pg", rawValue: string) => {
      const fieldKey = destinationFieldKey(child.name, side);
      const baseline = destinationBaseline[fieldKey] ?? "";
      if (rawValue === baseline) return;
      if (!rawValue) return;

      setFieldStatus((prev) => ({ ...prev, [fieldKey]: "saving" }));
      setFieldErrors((prev) => ({ ...prev, [fieldKey]: undefined }));

      try {
        const destination = normalizeEducationDestination(rawValue);
        const airtableKey = educationDestinationAirtableKey(child.airtableSlot, side);
        const res = await fetch(`/api/airtable/clients/${recordId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fields: { [airtableKey]: destination } }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error ?? `Save failed (${res.status})`);
        }
        onEducationSaved(data.client_data);
        setDestinationBaseline((prev) => ({ ...prev, [fieldKey]: destination }));
        setDestinationDraft((prev) => ({ ...prev, [fieldKey]: destination }));
        setFieldStatus((prev) => ({ ...prev, [fieldKey]: "saved" }));
      } catch (err) {
        setFieldStatus((prev) => ({ ...prev, [fieldKey]: "error" }));
        setFieldErrors((prev) => ({
          ...prev,
          [fieldKey]: err instanceof Error ? err.message : "Save failed",
        }));
      }
    },
    [destinationBaseline, onEducationSaved, recordId],
  );

  const handleDestinationChange = (
    child: EducationChildBlock,
    side: "ug" | "pg",
    value: string,
  ) => {
    const fieldKey = destinationFieldKey(child.name, side);
    setDestinationDraft((prev) => ({ ...prev, [fieldKey]: value }));
    setFieldStatus((prev) => ({ ...prev, [fieldKey]: "idle" }));
    if (!disabled && value) {
      void saveDestination(child, side, value);
    }
  };

  if (!blocks.length) return null;

  return (
    <div className="education-planning-section mt-0">
      <p className="mb-3 text-xs text-gray-500 dark:text-gray-400">
        Destination saves to Airtable on change. Target amount is used when you Make plan.
      </p>
      {blocks.map((child, idx) => (
        <div
          className={`child-education-block ${idx < blocks.length - 1 ? "mb-8" : ""}`}
          key={child.name}
        >
          <div className="mb-3 text-base font-semibold text-gray-800 dark:text-gray-100">
            🎓 {child.name}
            {child.age != null && (
              <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
                (Current age: {child.age})
              </span>
            )}
          </div>

          <div className="ug-section mb-4">
            <div className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
              Undergraduate ({child.ug.stream ?? "—"})
            </div>
            <StageTable
              stage={child.ug}
              value={targets[child.name]?.ug ?? ""}
              onChange={(v) => onTargetChange(child.name, "ug", v)}
              destinationValue={
                destinationDraft[destinationFieldKey(child.name, "ug")] ??
                destinationSelectValue(child.ug.destination)
              }
              onDestinationChange={(v) => handleDestinationChange(child, "ug", v)}
              destinationStatus={fieldStatus[destinationFieldKey(child.name, "ug")] ?? "idle"}
              destinationError={fieldErrors[destinationFieldKey(child.name, "ug")]}
              destinationDisabled={disabled}
            />
          </div>

          {child.hasPg && child.pg ? (
            <div className="pg-section">
              <div className="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Postgraduate ({child.pg.stream ?? "—"})
              </div>
              <StageTable
                stage={child.pg}
                value={targets[child.name]?.pg ?? ""}
                onChange={(v) => onTargetChange(child.name, "pg", v)}
                destinationValue={
                  destinationDraft[destinationFieldKey(child.name, "pg")] ??
                  destinationSelectValue(child.pg.destination)
                }
                onDestinationChange={(v) => handleDestinationChange(child, "pg", v)}
                destinationStatus={fieldStatus[destinationFieldKey(child.name, "pg")] ?? "idle"}
                destinationError={fieldErrors[destinationFieldKey(child.name, "pg")]}
                destinationDisabled={disabled}
              />
            </div>
          ) : (
            <div className="text-xs italic text-gray-400 dark:text-gray-500">
              No postgraduate education planned for {child.name}.
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
