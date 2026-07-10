"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ALL_SPOUSE_UI_PATHS,
  flattenSpouseFieldToAirtable,
  spouseValueToInput,
  valuesEqualForPath,
  type SpouseUiFieldPath,
} from "@/lib/spouseAirtableFields";

/** Nested category groups built in backend-airtable/main.py from flat Airtable fields. */
export type SpouseNestedCategory = Record<string, string | number | null | undefined>;

export type SpouseData = {
  spouse_name?: string;
  spouse_dob?: string;
  spouse_investment_mutual_fund_value?: number | null;
  spouse_investment_direct_equity_value?: number | null;
  esop?: SpouseNestedCategory;
  provident_fund?: SpouseNestedCategory;
  fd_bond?: SpouseNestedCategory;
};

type FieldStatus = "idle" | "saving" | "saved" | "error";

const FLAT_LABELS: Record<string, string> = {
  spouse_name: "Name",
  spouse_dob: "Date of Birth",
  spouse_investment_mutual_fund_value: "Mutual Funds",
  spouse_investment_direct_equity_value: "Direct Equity",
};

const NESTED_LABELS: Record<string, string> = {
  esop: "ESOP",
  provident_fund: "Provident Fund (PF)",
  fd_bond: "Fixed Deposit / Bond",
};

const SUBTYPE_LABELS: Record<string, string> = {
  vested: "Vested",
  unvested: "Unvested",
  current_value: "Current Value",
  monthly_contribution: "Monthly Contribution",
  invested_amount: "Invested Amount",
  interest_rate: "Interest Rate (%)",
  maturity_date: "Maturity Date",
};

const PERSONAL_PATHS: SpouseUiFieldPath[] = ["spouse_name", "spouse_dob"];
const INVESTMENT_PATHS: SpouseUiFieldPath[] = [
  "spouse_investment_mutual_fund_value",
  "spouse_investment_direct_equity_value",
];
const NESTED_SECTIONS: { key: string; label: string; paths: SpouseUiFieldPath[] }[] = [
  { key: "esop", label: NESTED_LABELS.esop, paths: ["esop.vested", "esop.unvested"] },
  {
    key: "provident_fund",
    label: NESTED_LABELS.provident_fund,
    paths: ["provident_fund.current_value", "provident_fund.monthly_contribution"],
  },
  {
    key: "fd_bond",
    label: NESTED_LABELS.fd_bond,
    paths: ["fd_bond.invested_amount", "fd_bond.interest_rate", "fd_bond.maturity_date"],
  },
];

const TH =
  "align-middle whitespace-nowrap px-4 py-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400";
const TD = "align-middle px-4 py-2 text-gray-700 dark:text-gray-300";
const ROW = "border-b border-gray-100 dark:border-gray-700";
const INPUT =
  "w-full rounded border border-gray-300 bg-white px-2 py-1 text-sm text-gray-900 focus:border-brand focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100";

function pathLabel(uiPath: SpouseUiFieldPath): string {
  if (uiPath in FLAT_LABELS) return FLAT_LABELS[uiPath];
  const sub = uiPath.split(".")[1];
  return SUBTYPE_LABELS[sub] ?? sub.replace(/_/g, " ");
}

function isNumericPath(uiPath: SpouseUiFieldPath): boolean {
  return (
    uiPath !== "spouse_name" &&
    uiPath !== "spouse_dob" &&
    uiPath !== "fd_bond.maturity_date"
  );
}

function isDatePath(uiPath: SpouseUiFieldPath): boolean {
  return uiPath === "spouse_dob" || uiPath === "fd_bond.maturity_date";
}

function draftFromSpouse(spouse: SpouseData): Record<SpouseUiFieldPath, string> {
  const draft = {} as Record<SpouseUiFieldPath, string>;
  for (const path of ALL_SPOUSE_UI_PATHS) {
    draft[path] = spouseValueToInput(path, spouse);
  }
  return draft;
}

function SectionLabel({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="mb-2 flex items-center gap-2">
      <span className="inline-flex h-5 w-5 items-center justify-center rounded bg-gray-900 text-[10px] text-white dark:bg-gray-100 dark:text-gray-900">
        {icon}
      </span>
      <span className="text-[11px] font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400">
        {text}
      </span>
    </div>
  );
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

export function SpouseDetailsPanel({
  recordId,
  spouse,
  onSpouseSaved,
  disabled = false,
}: {
  recordId: string;
  spouse: SpouseData;
  onSpouseSaved: (clientData: Record<string, unknown>) => void;
  disabled?: boolean;
}) {
  const [draft, setDraft] = useState<Record<SpouseUiFieldPath, string>>(() =>
    draftFromSpouse(spouse),
  );
  const [savedBaseline, setSavedBaseline] = useState<Record<SpouseUiFieldPath, string>>(() =>
    draftFromSpouse(spouse),
  );
  const [fieldStatus, setFieldStatus] = useState<Partial<Record<SpouseUiFieldPath, FieldStatus>>>(
    {},
  );
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<SpouseUiFieldPath, string>>>({});

  useEffect(() => {
    const next = draftFromSpouse(spouse);
    setDraft(next);
    setSavedBaseline(next);
    setFieldStatus({});
    setFieldErrors({});
    // Reset only when switching clients; field saves update baseline locally.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordId]);

  const saveField = useCallback(
    async (uiPath: SpouseUiFieldPath) => {
      const current = draft[uiPath] ?? "";
      const baseline = savedBaseline[uiPath] ?? "";
      if (valuesEqualForPath(uiPath, current, baseline)) return;

      setFieldStatus((prev) => ({ ...prev, [uiPath]: "saving" }));
      setFieldErrors((prev) => ({ ...prev, [uiPath]: undefined }));

      try {
        const fields = flattenSpouseFieldToAirtable(uiPath, current);
        const res = await fetch(`/api/airtable/clients/${recordId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fields }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error ?? `Save failed (${res.status})`);
        }
        onSpouseSaved(data.client_data);
        setSavedBaseline((prev) => ({ ...prev, [uiPath]: current }));
        setFieldStatus((prev) => ({ ...prev, [uiPath]: "saved" }));
      } catch (err) {
        setFieldStatus((prev) => ({ ...prev, [uiPath]: "error" }));
        setFieldErrors((prev) => ({
          ...prev,
          [uiPath]: err instanceof Error ? err.message : "Save failed",
        }));
      }
    },
    [draft, onSpouseSaved, recordId, savedBaseline],
  );

  const handleChange = (uiPath: SpouseUiFieldPath, value: string) => {
    setDraft((prev) => ({ ...prev, [uiPath]: value }));
    setFieldStatus((prev) => ({ ...prev, [uiPath]: "idle" }));
  };

  const handleBlur = (uiPath: SpouseUiFieldPath) => {
    if (!disabled) void saveField(uiPath);
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    uiPath: SpouseUiFieldPath,
  ) => {
    if (e.key === "Enter") {
      e.currentTarget.blur();
      if (!disabled) void saveField(uiPath);
    }
  };

  const renderFieldRow = (uiPath: SpouseUiFieldPath) => {
    const numeric = isNumericPath(uiPath);
    const status = fieldStatus[uiPath] ?? "idle";
    const hint = statusText(status, fieldErrors[uiPath]);

    return (
      <tr key={uiPath} className={ROW}>
        <td className={`${TD} w-1/2 text-left font-medium text-gray-500 dark:text-gray-400`}>
          {pathLabel(uiPath)}
        </td>
        <td className={`${TD} ${numeric ? "text-right" : "text-left"}`}>
          <input
            type={isDatePath(uiPath) ? "date" : numeric ? "number" : "text"}
            min={numeric ? "0" : undefined}
            step={uiPath === "fd_bond.interest_rate" ? "0.01" : undefined}
            inputMode={numeric ? "numeric" : undefined}
            value={draft[uiPath] ?? ""}
            disabled={disabled || status === "saving"}
            onChange={(e) => handleChange(uiPath, e.target.value)}
            onBlur={() => handleBlur(uiPath)}
            onKeyDown={(e) => handleKeyDown(e, uiPath)}
            className={`${INPUT} ${numeric ? "text-right" : "text-left"} ${statusBorder(status)}`}
          />
          {hint ? (
            <p
              className={`mt-1 text-[10px] ${
                status === "error"
                  ? "text-red-500"
                  : status === "saved"
                    ? "text-green-600 dark:text-green-400"
                    : "text-gray-400"
              }`}
            >
              {hint}
            </p>
          ) : null}
        </td>
      </tr>
    );
  };

  return (
    <div className="spouse-details-panel space-y-4">
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Edit spouse fields inline — changes save to Airtable on blur or Enter.
      </p>

      <section>
        <SectionLabel icon="👤" text="Personal Details" />
        <table className="w-full border-collapse text-xs">
          <tbody>{PERSONAL_PATHS.map(renderFieldRow)}</tbody>
        </table>
      </section>

      <section>
        <SectionLabel icon="💼" text="Spouse Investments" />
        <table className="w-full border-collapse text-xs">
          <tbody>{INVESTMENT_PATHS.map(renderFieldRow)}</tbody>
        </table>
      </section>

      <section className="space-y-4">
        {NESTED_SECTIONS.map(({ key, label, paths }) => (
          <div key={key}>
            <SectionLabel icon="📋" text={label} />
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className={`bg-gray-50 dark:bg-gray-800 ${ROW}`}>
                  <th className={`${TH} text-left`}>Field</th>
                  <th className={`${TH} text-right`}>Value</th>
                </tr>
              </thead>
              <tbody>{paths.map(renderFieldRow)}</tbody>
            </table>
          </div>
        ))}
      </section>
    </div>
  );
}

export function spouseFromClientData(clientData: {
  spouse_name?: string;
  spouse_dob?: string;
  spouse?: SpouseData | null;
}): SpouseData {
  return {
    spouse_name: clientData.spouse?.spouse_name ?? clientData.spouse_name ?? "",
    spouse_dob: clientData.spouse?.spouse_dob ?? clientData.spouse_dob ?? "",
    spouse_investment_mutual_fund_value:
      clientData.spouse?.spouse_investment_mutual_fund_value ?? null,
    spouse_investment_direct_equity_value:
      clientData.spouse?.spouse_investment_direct_equity_value ?? null,
    esop: clientData.spouse?.esop ?? {},
    provident_fund: clientData.spouse?.provident_fund ?? {},
    fd_bond: clientData.spouse?.fd_bond ?? {},
  };
}

export function mergeSpouseData(
  fromClient?: SpouseData | null,
  fromPlan?: SpouseData | null,
  fallback?: { spouse_name?: string; spouse_dob?: string },
): SpouseData | null {
  const merged: SpouseData = {
    spouse_name: fromClient?.spouse_name ?? fallback?.spouse_name,
    spouse_dob: fromClient?.spouse_dob ?? fallback?.spouse_dob,
    ...fromClient,
    ...fromPlan,
  };
  if (!merged.spouse_name && !merged.spouse_dob) return null;
  return merged;
}
