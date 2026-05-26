"use client";

/** Nested category groups built in backend/airtable_main.py from flat Airtable fields. */
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

const FLAT_SCALAR_KEYS = [
  "spouse_name",
  "spouse_dob",
  "spouse_investment_mutual_fund_value",
  "spouse_investment_direct_equity_value",
] as const;

const NESTED_CATEGORY_KEYS = ["esop", "provident_fund", "fd_bond"] as const;

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
  interest_rate: "Interest Rate",
  maturity_date: "Maturity Date",
};

const TH =
  "align-middle whitespace-nowrap px-4 py-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400";
const TD = "align-middle px-4 py-2 text-gray-700 dark:text-gray-300";
const ROW = "border-b border-gray-100 dark:border-gray-700";

function fmtInr(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  if (n >= 1_00_00_000) return `₹${(n / 1_00_00_000).toFixed(2)}Cr`;
  if (n >= 1_00_000) return `₹${(n / 1_00_000).toFixed(2)}L`;
  return `₹${n.toLocaleString("en-IN")}`;
}

function fmtPct(r: number | null | undefined): string {
  return r ? `${(r * 100).toFixed(2)}%` : "—";
}

function formatSubtypeValue(key: string, value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "number") {
    if (key === "interest_rate") return fmtPct(value);
    if (key === "monthly_contribution") return `${fmtInr(value)} /mo`;
    return fmtInr(value);
  }
  return String(value);
}

function formatFlatValue(key: string, value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "number") return fmtInr(value);
  return String(value);
}

function isNumericKey(key: string): boolean {
  return key !== "spouse_name" && key !== "spouse_dob" && key !== "maturity_date";
}

function isNestedCategory(value: unknown): value is SpouseNestedCategory {
  if (value == null) return false;
  if (Array.isArray(value)) return value.length > 0 && typeof value[0] === "object";
  return typeof value === "object";
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

function FlatFieldsTable({
  rows,
}: {
  rows: { label: string; value: string; numeric?: boolean }[];
}) {
  if (!rows.length) return null;

  return (
    <table className="w-full border-collapse text-xs">
      <tbody>
        {rows.map(({ label, value, numeric }) => (
          <tr key={label} className={ROW}>
            <td className={`${TD} w-1/2 text-left font-medium text-gray-500 dark:text-gray-400`}>
              {label}
            </td>
            <td
              className={`${TD} font-semibold text-gray-900 dark:text-gray-100 ${
                numeric ? "text-right" : "text-left"
              }`}
            >
              {value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function NestedCategoryTable({ label, value }: { label: string; value: SpouseNestedCategory | unknown[] }) {
  if (Array.isArray(value)) {
    if (!value.length || typeof value[0] !== "object") return null;
    const columns = Object.keys(value[0] as object);
    const numericTotals: Record<string, number> = {};
    columns.forEach((col) => {
      const sum = value.reduce((s: number, row) => {
        const v = (row as Record<string, unknown>)[col];
        return s + (typeof v === "number" ? v : 0);
      }, 0);
      if (value.some((r) => typeof (r as Record<string, unknown>)[col] === "number")) {
        numericTotals[col] = sum;
      }
    });

    const colAlign = (col: string, i: number) => {
      if (i === 0) return "text-left";
      if (typeof (value[0] as Record<string, unknown>)[col] === "number") return "text-right";
      return "text-left";
    };

    return (
      <div className="mb-4">
        <SectionLabel icon="📋" text={label} />
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className={`bg-gray-50 dark:bg-gray-800 ${ROW}`}>
              {columns.map((col, i) => (
                <th key={col} className={`${TH} ${colAlign(col, i)}`}>
                  {SUBTYPE_LABELS[col] ?? col.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {value.map((row, idx) => (
              <tr key={idx} className={`${ROW} hover:bg-gray-50 dark:hover:bg-gray-800/50`}>
                {columns.map((col, i) => (
                  <td key={col} className={`${TD} ${colAlign(col, i)}`}>
                    {formatSubtypeValue(col, (row as Record<string, unknown>)[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
          {Object.keys(numericTotals).length > 0 && (
            <tfoot>
              <tr className={`bg-gray-50 font-semibold dark:bg-gray-800 ${ROW}`}>
                {columns.map((col, i) => (
                  <td
                    key={col}
                    className={`${TD} text-gray-900 dark:text-gray-100 ${i === 0 ? "text-left" : "text-right"}`}
                  >
                    {i === 0 ? "Total" : numericTotals[col] != null ? fmtInr(numericTotals[col]) : ""}
                  </td>
                ))}
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    );
  }

  const entries = Object.entries(value).filter(([, v]) => v != null && v !== "");
  if (!entries.length) return null;

  const total = entries.reduce((s, [, v]) => s + (typeof v === "number" ? v : 0), 0);

  return (
    <div className="mb-4">
      <SectionLabel icon="📋" text={label} />
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className={`bg-gray-50 dark:bg-gray-800 ${ROW}`}>
            <th className={`${TH} text-left`}>Type</th>
            <th className={`${TH} text-right`}>Value</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([subType, subVal]) => (
            <tr key={subType} className={`${ROW} hover:bg-gray-50 dark:hover:bg-gray-800/50`}>
              <td className={`${TD} text-left text-gray-900 dark:text-gray-100`}>
                {SUBTYPE_LABELS[subType] ?? subType.replace(/_/g, " ")}
              </td>
              <td className={`${TD} text-right font-medium text-gray-900 dark:text-gray-100`}>
                {formatSubtypeValue(subType, subVal)}
              </td>
            </tr>
          ))}
        </tbody>
        {total > 0 && (
          <tfoot>
            <tr className={`bg-gray-50 font-semibold dark:bg-gray-800 ${ROW}`}>
              <td className={`${TD} text-left text-gray-700 dark:text-gray-300`}>Total</td>
              <td className={`${TD} text-right text-gray-900 dark:text-gray-100`}>{fmtInr(total)}</td>
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  );
}

export function SpouseDetailsPanel({ spouse }: { spouse: SpouseData }) {
  const personalRows: { label: string; value: string; numeric?: boolean }[] = [];
  const investmentRows: { label: string; value: string; numeric?: boolean }[] = [];

  for (const key of FLAT_SCALAR_KEYS) {
    const raw = spouse[key];
    const label = FLAT_LABELS[key];
    const formatted = formatFlatValue(key, raw);
    const row = { label, value: formatted, numeric: isNumericKey(key) };
    if (key === "spouse_name" || key === "spouse_dob") {
      personalRows.push(row);
    } else if (raw != null && raw !== "") {
      investmentRows.push(row);
    }
  }

  const nestedBlocks = NESTED_CATEGORY_KEYS.flatMap((key) => {
    const value = spouse[key];
    if (!isNestedCategory(value)) return [];
    return [{ key, label: NESTED_LABELS[key] ?? key, value }];
  });

  return (
    <div className="spouse-details-panel space-y-4">
      <section>
        <SectionLabel icon="👤" text="Personal Details" />
        <FlatFieldsTable rows={personalRows} />
      </section>

      {investmentRows.length > 0 && (
        <section>
          <SectionLabel icon="💼" text="Spouse Investments" />
          <FlatFieldsTable rows={investmentRows} />
        </section>
      )}

      {nestedBlocks.length > 0 && (
        <section className="space-y-0">
          {nestedBlocks.map(({ key, label, value }) => (
            <NestedCategoryTable key={key} label={label} value={value} />
          ))}
        </section>
      )}
    </div>
  );
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
