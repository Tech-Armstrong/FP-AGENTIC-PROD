"use client";

import type { EducationChildBlock, EducationStageView } from "@/lib/educationPlanningView";

const TH =
  "align-middle px-4 py-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400";
const TD = "align-middle px-4 py-2 text-gray-700 dark:text-gray-300";

function fmtYear(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return String(n);
}

/** Target Amount = user-entered final corpus (no inflation). */
function StageTable({
  stage,
  value,
  onChange,
}: {
  stage: EducationStageView;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <table className="w-full border-collapse text-xs">
      <thead>
        <tr className="border-b border-gray-100 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
          <th className={`${TH} text-left`}>Stream</th>
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
  blocks,
  targets,
  onTargetChange,
}: {
  blocks: EducationChildBlock[];
  targets: Record<string, { ug?: string; pg?: string }>;
  onTargetChange: (childName: string, side: "ug" | "pg", value: string) => void;
}) {
  if (!blocks.length) return null;

  return (
    <div className="education-planning-section mt-0">
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
