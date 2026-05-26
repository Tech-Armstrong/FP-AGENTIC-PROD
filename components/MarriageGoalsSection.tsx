"use client";

export type MarriageGoalRow = {
  goal_name?: string;
  child_name?: string;
  target_year?: number | string | null;
  current_cost?: number | null;
  future_cost?: number | null;
  status?: "funded" | "partial" | "not_funded" | string;
};

function fmtInr(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function FundedBadge({ status }: { status?: string }) {
  const s = (status ?? "").toLowerCase();
  if (s === "funded") {
    return (
      <span className="font-medium text-emerald-600 dark:text-emerald-400">Funded</span>
    );
  }
  if (s === "partial" || s === "partial_funded") {
    return (
      <span className="font-medium text-amber-600 dark:text-amber-400">Partial</span>
    );
  }
  return (
    <span className="font-medium text-red-500 dark:text-red-400">Unfunded</span>
  );
}

export function MarriageGoalsSection({ goals }: { goals: MarriageGoalRow[] }) {
  if (!goals.length) return null;

  return (
    <div className="marriage-goals-section">
      <div className="mb-2 flex items-center gap-2">
        <span className="text-[11px] font-bold uppercase tracking-widest text-gray-600 dark:text-gray-400">
          Marriage Goals
        </span>
      </div>

      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-gray-100 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
            <th className="align-middle px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Child / Goal
            </th>
            <th className="align-middle px-4 py-2 text-left text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Target Year
            </th>
            <th className="align-middle px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Current Cost
            </th>
            <th className="align-middle px-4 py-2 text-right text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Future Cost
            </th>
            <th className="align-middle px-4 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Funded
            </th>
          </tr>
        </thead>
        <tbody>
          {goals.map((goal, idx) => (
            <tr
              key={`${goal.goal_name}-${idx}`}
              className="border-b border-gray-100 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800/50"
            >
              <td className="align-middle px-4 py-2 text-left text-gray-900 dark:text-gray-100">
                {goal.child_name ?? goal.goal_name ?? `Child ${idx + 1}`}
              </td>
              <td className="align-middle px-4 py-2 text-left text-gray-700 dark:text-gray-300">
                {goal.target_year ?? "—"}
              </td>
              <td className="align-middle px-4 py-2 text-right text-gray-700 dark:text-gray-300">
                {fmtInr(goal.current_cost)}
              </td>
              <td className="align-middle px-4 py-2 text-right font-semibold text-gray-900 dark:text-gray-100">
                {fmtInr(goal.future_cost)}
              </td>
              <td className="align-middle px-4 py-2 text-center">
                <FundedBadge status={goal.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
