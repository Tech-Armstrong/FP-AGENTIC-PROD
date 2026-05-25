"use client";

import type { ReactNode } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

export type SsySummaryEntry = {
  child_name?: string;
  total_fv?: number | null;
  total_withdrawn?: number | null;
  remaining_balance?: number | null;
  maturity_year?: number | null;
  locked?: boolean;
};

function fmtInr(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function ReviewSectionTitle({
  icon: Icon,
  children,
}: {
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-3.5 flex items-center gap-2 border-b-2 border-sky-200 pb-1.5 text-[0.82rem] font-bold uppercase tracking-[0.07em] text-[#2b6cb0] dark:border-sky-800 dark:text-sky-300">
      <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900">
        <Icon className="h-3 w-3" strokeWidth={2.5} />
      </span>
      {children}
    </div>
  );
}

export function SsyTrackerSection({ rows }: { rows: SsySummaryEntry[] }) {
  if (!rows.length) return null;

  return (
    <div className="mb-7">
      <ReviewSectionTitle icon={Star}>SSY Tracker</ReviewSectionTitle>
      <div className="space-y-3">
        {rows.map((entry, idx) => {
          const remaining = Number(entry.remaining_balance ?? 0);
          const maturityYear = entry.maturity_year ?? "—";
          const locked = Boolean(entry.locked);
          const remainingClass =
            remaining > 0
              ? "text-emerald-800 dark:text-emerald-400"
              : "text-slate-500 dark:text-slate-400";

          let statusBadge: ReactNode = null;
          if (locked) {
            statusBadge = (
              <span className="ml-2 inline-block rounded border border-violet-300 bg-violet-50 px-2 py-0.5 text-[0.72rem] font-semibold text-violet-800 dark:border-violet-700 dark:bg-violet-950/50 dark:text-violet-200">
                Locked until {maturityYear}
              </span>
            );
          } else if (remaining > 0) {
            statusBadge = (
              <span className="ml-2 inline-block rounded border border-emerald-300 bg-emerald-50 px-2 py-0.5 text-[0.72rem] font-semibold text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-200">
                Available at maturity {maturityYear}
              </span>
            );
          }

          return (
            <div
              key={`${entry.child_name}-${idx}`}
              className="rounded-lg border border-violet-200 bg-violet-50/80 p-3.5 sm:p-4 dark:border-violet-800 dark:bg-violet-950/30"
            >
              <div className="mb-2.5 flex flex-wrap items-center gap-1">
                <strong className="text-[0.95rem] text-slate-900 dark:text-slate-100">
                  {entry.child_name ?? "Child"}
                </strong>
                {statusBadge}
              </div>
              <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-2 text-[0.83rem]">
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Total FV at goal</span>
                  <br />
                  <strong className="text-slate-800 dark:text-slate-200">
                    {fmtInr(entry.total_fv ?? undefined)}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Total withdrawn</span>
                  <br />
                  <strong className="text-slate-800 dark:text-slate-200">
                    {fmtInr(entry.total_withdrawn ?? undefined)}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Remaining balance</span>
                  <br />
                  <strong className={cn(remainingClass)}>
                    {fmtInr(entry.remaining_balance ?? undefined)}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Maturity year</span>
                  <br />
                  <strong className="text-slate-800 dark:text-slate-200">{maturityYear}</strong>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
