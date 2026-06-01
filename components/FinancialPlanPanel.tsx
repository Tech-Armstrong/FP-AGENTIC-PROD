"use client";

import * as React from "react";
import {
  Activity,
  ArrowRightLeft,
  Heart,
  Landmark,
  PiggyBank,
  Shield,
  Sparkles,
  Target,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { EducationChildBlock } from "@/lib/educationPlanningView";
import { SsyTrackerSection, type SsySummaryEntry } from "./SsyTrackerSection";
import { PieChart } from "./generative-ui/PieChart";

type SchemeBreakdownRow = {
  type?: string;
  label?: string;
  amount?: number | null;
  fv?: number | null;
};

type FundedFromRow = Record<string, unknown> & {
  breakdown?: SchemeBreakdownRow[];
  total_fv?: number;
};

type GoalAlloc = {
  goal_name?: string;
  corpus_needed?: number;
  corpus_gap?: number;
  target_corpus?: number;
  target_year?: number;
  /** Education goals only — program start/end for plan card display. */
  start_year?: number | null;
  end_year?: number | null;
  filter?: { type?: string }[];
  notes?: string[];
  funded_from_preview?: FundedFromRow[];
};

export type PlanSummary = {
  client_name?: string;
  monthly_surplus?: number | null;
  risk_appetite?: { risk_appetite?: string; reason?: string } | Record<string, unknown>;
  liquidity_ratio?: number | null;
  liquidity_flag?: string | null;
  flexibility?: string | null;
  spending_behavior?: Record<string, unknown> | null;
  ending_liquid_pool?: number | null;
  ending_monthly_surplus?: number | null;
  sorted_goals_preview?: {
    goal_name?: string;
    priority_score?: number;
    target_year?: number;
    corpus_needed?: number;
  }[];
  goal_allocation_preview?: GoalAlloc[];
  loans_exist?: boolean;
  final_unused_monthly_surplus?: number | null;
  retirement_goal_preview?: unknown;
  ssy_summary_preview?: SsySummaryEntry[];
  term_insurance_requirement?: {
    section?: string;
    total_cover_required?: number;
    breakdown?: Record<string, number>;
    note?: string;
  } | null;
  spouse_preview?: Record<string, unknown> | null;
  marriage_goals_preview?: Record<string, unknown>[] | null;
  education_targets_preview?: Record<string, unknown>[] | null;
  education_planning_preview?: Record<string, unknown>[] | null;
  real_estate_preview?: Record<string, unknown>[] | null;
};

export type PlanResponse = { ok?: boolean; summary?: PlanSummary; detail?: string };

export type PlanOverrides = {
  epf_rate?: number;
  ppf_rate?: number;
  nps_rate?: number;
  mf_expected_return?: number;
};

/** @deprecated Use PlanOverrides — kept for existing imports */
export type RetirementRateOverrides = PlanOverrides;

/** Decimal values actually used for a plan run (POST overrides merged with originals). */
export type AppliedRates = {
  epf: number | null;
  ppf: number | null;
  nps: number | null;
  mfExpectedReturn: number | null;
};

export function emptyAppliedRates(): AppliedRates {
  return {
    epf: null,
    ppf: null,
    nps: null,
    mfExpectedReturn: null,
  };
}

export function resolveAppliedRates(
  original: AppliedRates,
  overrides: PlanOverrides | null,
): AppliedRates {
  if (!overrides) {
    return { ...original };
  }
  return {
    epf: overrides.epf_rate ?? original.epf,
    ppf: overrides.ppf_rate ?? original.ppf,
    nps: overrides.nps_rate ?? original.nps,
    mfExpectedReturn: overrides.mf_expected_return ?? original.mfExpectedReturn,
  };
}

export type PlanTab = {
  id: string;
  label: string;
  overrides: PlanOverrides | null;
  /** Values sent to the workflow for this tab (frozen at run kickoff). */
  appliedRates: AppliedRates;
  summary: PlanSummary;
};

const STEPS = [
  "Loading client data",
  "Calculating asset allocation & ratios",
  "Prioritising financial goals",
  "Allocating surplus & lumpsum",
  "Planning loan prepayments",
  "Selecting optimal strategy",
  "Finalising plan summary",
];

function fmtInr(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function displayFundingType(t: string): string {
  const s = String(t || "");
  if (s === "Retirement Schemes") return "Retirement Schemes";
  if (s === "rsu_funds") return "RSU";
  if (s === "SIP" || s.includes("sip")) return "SIP";
  if (s.includes("freed")) return "Freed EMI";
  if (s.includes("lump")) return "Lumpsum";
  if (s.includes("ssy")) return "SSY";
  if (s.includes("retirement") || s === "future_values_retirement_investments")
    return "Retirement";
  return s.replace(/_/g, " ") || "—";
}

function fundingBadgeClass(displayType: string): string {
  const d = displayType.toUpperCase();
  if (d.includes("SIP")) return "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-200";
  if (d.includes("FREED")) return "bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-200";
  if (d.includes("LUMP")) return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200";
  if (d.includes("SSY")) return "bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-200";
  if (d.includes("RSU")) return "bg-orange-50 text-orange-800 dark:bg-orange-950 dark:text-orange-200";
  if (d === "EPF" || d === "PPF" || d === "NPS" || d === "ULIP")
    return "bg-purple-100 text-purple-900 dark:bg-purple-950 dark:text-purple-200";
  if (d.includes("RETIREMENT")) return "bg-purple-100 text-purple-900 dark:bg-purple-950 dark:text-purple-200";
  return "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200";
}

function RetirementSchemeBreakdown({
  totalFv,
  breakdown,
}: {
  totalFv?: number;
  breakdown: SchemeBreakdownRow[];
}) {
  return (
    <tr className="bg-violet-50/60 dark:bg-violet-950/30">
      <td colSpan={6} className="px-3.5 py-3">
        <div className="mb-2.5 flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "inline-block rounded-xl px-2.5 py-0.5 text-[0.75rem] font-bold",
              fundingBadgeClass("Retirement Schemes"),
            )}
          >
            Retirement Schemes
          </span>
          <span className="text-[0.8rem] text-slate-500 dark:text-slate-400">Total future value:</span>
          <strong className="text-purple-900 dark:text-purple-300">{fmtInr(totalFv)}</strong>
        </div>
        <div className="flex flex-wrap gap-2.5">
          {breakdown.map((s, j) => {
            const label = s.label || s.type || "Scheme";
            const schemeType = s.type || "Retirement Scheme";
            return (
              <div
                key={j}
                className="min-w-[130px] rounded-lg border border-violet-200 bg-white px-3.5 py-2.5 dark:border-violet-800 dark:bg-gray-900"
              >
                <span
                  className={cn(
                    "mb-2 inline-block rounded-lg px-2 py-0.5 text-[0.72rem] font-bold",
                    fundingBadgeClass(schemeType),
                  )}
                >
                  {label}
                </span>
                <div className="flex gap-5 text-[0.8rem]">
                  <div>
                    <div className="mb-0.5 text-[0.68rem] font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Current value
                    </div>
                    <div className="font-semibold text-slate-800 dark:text-slate-200">
                      {fmtInr(s.amount ?? undefined)}
                    </div>
                  </div>
                  <div>
                    <div className="mb-0.5 text-[0.68rem] font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Future value
                    </div>
                    <div className="font-bold text-purple-900 dark:text-purple-300">
                      {fmtInr(s.fv ?? undefined)}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </td>
    </tr>
  );
}

function deriveGoalStatus(g: GoalAlloc): "funded" | "partial_funded" | "not_funded" {
  const filters = g.filter || [];
  const types = filters.map((f) => (f.type || "").toLowerCase());
  if (types.includes("unfunded")) return "not_funded";
  if (types.includes("partial_funded")) return "partial_funded";
  if (types.includes("funded")) return "funded";
  const gap = Number(g.corpus_gap ?? 0);
  if (gap > 0) return "partial_funded";
  return "funded";
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

function KvGrid({
  items,
}: {
  items: { label: string; value: React.ReactNode }[];
}) {
  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
      {items.map(({ label, value }) => (
        <div
          key={label}
          className="rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 dark:border-slate-700 dark:bg-slate-800/60"
        >
          <div className="mb-1 text-[0.72rem] font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {label}
          </div>
          <div className="break-words text-[0.95rem] font-semibold text-slate-700 dark:text-slate-200">
            {value}
          </div>
        </div>
      ))}
    </div>
  );
}

function FundingTable({ rows }: { rows: FundedFromRow[] }) {
  if (!rows.length) {
    return (
      <span className="text-[0.8rem] text-slate-400 dark:text-slate-500">No allocation recorded</span>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse text-[0.83rem]">
        <thead>
          <tr className="border-b-2 border-slate-200 bg-slate-100 text-left text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400">
            <th className="whitespace-nowrap px-2.5 py-1.5 font-semibold">Source</th>
            <th className="whitespace-nowrap px-2.5 py-1.5 font-semibold">Amount</th>
            <th className="whitespace-nowrap px-2.5 py-1.5 font-semibold">From</th>
            <th className="whitespace-nowrap px-2.5 py-1.5 font-semibold">To</th>
            <th className="whitespace-nowrap px-2.5 py-1.5 font-semibold">Rate</th>
            <th className="whitespace-nowrap px-2.5 py-1.5 font-semibold">FV</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((f, i) => {
            const rawType = String(f.type || "");
            if (rawType === "Retirement Schemes") {
              const breakdown = (f.breakdown as SchemeBreakdownRow[]) || [];
              if (breakdown.length > 0) {
                return (
                  <RetirementSchemeBreakdown
                    key={i}
                    totalFv={f.total_fv as number | undefined}
                    breakdown={breakdown}
                  />
                );
              }
              return (
                <tr key={i} className="border-b border-slate-200 bg-violet-50/40 dark:border-slate-700 dark:bg-violet-950/30">
                  <td className="px-2.5 py-1.5">
                    <span
                      className={cn(
                        "inline-block rounded-xl px-2.5 py-0.5 text-[0.75rem] font-bold",
                        fundingBadgeClass("Retirement Schemes"),
                      )}
                    >
                      Retirement Schemes
                    </span>
                  </td>
                  <td colSpan={4} className="px-2.5 py-1.5 text-slate-500 dark:text-slate-400">
                    Existing retirement investments
                  </td>
                  <td className="px-2.5 py-1.5 font-semibold text-purple-900 dark:text-purple-300">
                    {fmtInr(f.total_fv as number | undefined)}
                  </td>
                </tr>
              );
            }
            const display = displayFundingType(rawType);
            const badge = fundingBadgeClass(display);
            const monthly = f.monthly as number | undefined;
            const amountUsed = f.amount_used as number | undefined;
            const amount = f.amount as number | undefined;
            const principal = f.principal_used_today as number | undefined;
            const fv =
              (f.fv_contribution as number | undefined) ??
              (f.fv as number | undefined);
            const fromY = f.from_year as number | string | undefined;
            const toY = f.to_year as number | string | undefined;
            const rate = f.rate as string | undefined;
            const source = f.source as string | undefined;

            let amtCell: React.ReactNode = "—";
            if (rawType === "rsu_funds" && amountUsed != null)
              amtCell = fmtInr(amountUsed);
            else if (monthly != null) amtCell = `${fmtInr(monthly)}/mo`;
            else if (amount != null) amtCell = fmtInr(amount);
            else if (principal != null) amtCell = fmtInr(principal);

            return (
              <tr key={i} className="border-b border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/50">
                <td className="whitespace-nowrap px-2.5 py-1.5 text-slate-800 dark:text-slate-200">
                  <span
                    className={cn(
                      "inline-block rounded-xl px-2.5 py-0.5 text-[0.75rem] font-bold",
                      badge,
                    )}
                  >
                    {display}
                  </span>
                  {source ? (
                    <div className="mt-1 text-[0.78rem] text-slate-500 dark:text-slate-400">{source}</div>
                  ) : null}
                </td>
                <td className="whitespace-nowrap px-2.5 py-1.5">{amtCell}</td>
                <td className="whitespace-nowrap px-2.5 py-1.5">
                  {fromY != null && fromY !== "" ? String(fromY) : "—"}
                </td>
                <td className="whitespace-nowrap px-2.5 py-1.5">
                  {toY != null && toY !== "" ? String(toY) : "—"}
                </td>
                <td className="whitespace-nowrap px-2.5 py-1.5">
                  {rate != null ? String(rate) : "—"}
                </td>
                <td className="whitespace-nowrap px-2.5 py-1.5">
                  {fv != null ? fmtInr(fv) : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function PlanWarningOverlay({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/80 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="plan-warning-title"
    >
      <div className="mx-4 w-full max-w-[460px] rounded-2xl bg-white px-10 py-10 text-center shadow-2xl dark:bg-gray-900">
        <h2
          id="plan-warning-title"
          className="mb-4 text-lg font-bold text-slate-900 dark:text-slate-100"
        >
          Education target required
        </h2>
        <p className="mb-6 text-[0.9rem] text-slate-600 dark:text-slate-300">
          Please enter the education target amount for each child in the Education Planning section
          before generating the plan.
        </p>
        <button
          type="button"
          onClick={onClose}
          className="inline-flex items-center justify-center rounded-lg bg-[#2b6cb0] px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-[#2c5282]"
        >
          OK
        </button>
      </div>
    </div>
  );
}

function PlanGeneratingOverlay({ activeStep }: { activeStep: number }) {
  const pct = Math.min(100, Math.round(((activeStep + 1) / STEPS.length) * 82));

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/80 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="plan-overlay-title"
    >
      <div className="mx-4 w-full max-w-[460px] rounded-2xl bg-white px-10 py-10 text-center shadow-2xl dark:bg-gray-900">
        <div
          className="mx-auto mb-5 h-14 w-14 animate-spin rounded-full border-[5px] border-slate-200 border-t-[#1a365d] dark:border-slate-700 dark:border-t-sky-400"
          aria-hidden
        />
        <h2
          id="plan-overlay-title"
          className="mb-1.5 text-lg font-bold text-slate-900 dark:text-slate-100"
        >
          Generating Financial Plan
        </h2>
        <p className="mb-6 text-[0.83rem] text-slate-500 dark:text-slate-400">
          Running AI workflow… this may take 1–3 minutes.
        </p>
        <div className="mb-5 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
          <div
            className="h-full rounded-full bg-[#1a365d] transition-[width] duration-1000 ease-out dark:bg-sky-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="space-y-1 text-left text-[0.82rem]">
          {STEPS.map((label, i) => (
            <div
              key={label}
              className={cn(
                "flex items-center gap-2.5 py-1 transition-colors",
                i < activeStep && "font-medium text-emerald-700 dark:text-emerald-400",
                i === activeStep && "font-semibold text-slate-900 dark:text-slate-100",
                i > activeStep && "text-slate-400 dark:text-slate-500",
              )}
            >
              <span
                className={cn(
                  "h-2 w-2 shrink-0 rounded-full",
                  i < activeStep && "bg-emerald-500",
                  i === activeStep && "bg-[#1a365d] shadow-[0_0_0_3px_rgba(26,54,93,0.2)]",
                  i > activeStep && "bg-slate-200 dark:bg-slate-600",
                )}
              />
              {label}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function FinancialPlanPanel({
  recordId,
  disabled,
  planOverrides,
  originalRates,
  planTabs,
  activeTabId,
  onActiveTabChange,
  onPlanComplete,
  educationBlocks,
  educationTargets,
}: {
  recordId: string | null;
  disabled?: boolean;
  planOverrides?: PlanOverrides | null;
  originalRates: AppliedRates;
  planTabs: PlanTab[];
  activeTabId: string | null;
  onActiveTabChange: (id: string) => void;
  onPlanComplete: (payload: {
    overrides: PlanOverrides | null;
    appliedRates: AppliedRates;
    summary: PlanSummary;
    label?: string;
  }) => void;
  educationBlocks?: EducationChildBlock[];
  educationTargets?: Record<string, { ug?: string; pg?: string }>;
}) {
  const [loading, setLoading] = React.useState(false);
  const [showWarning, setShowWarning] = React.useState(false);
  const [overlayStep, setOverlayStep] = React.useState(0);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<{
    msg: string;
    type: "info" | "success" | "error";
  } | null>(null);

  React.useEffect(() => {
    setError(null);
    setStatus(null);
  }, [recordId]);

  React.useEffect(() => {
    if (!loading) {
      setOverlayStep(0);
      return;
    }
    const t0 = window.setTimeout(() => setOverlayStep(1), 5000);
    const t1 = window.setTimeout(() => setOverlayStep(2), 15000);
    const t2 = window.setTimeout(() => setOverlayStep(3), 28000);
    const t3 = window.setTimeout(() => setOverlayStep(4), 45000);
    const t4 = window.setTimeout(() => setOverlayStep(5), 62000);
    const t5 = window.setTimeout(() => setOverlayStep(6), 78000);
    return () => {
      clearTimeout(t0);
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      clearTimeout(t5);
    };
  }, [loading]);

  const parseAmt = (v?: string): number | null => {
    if (v == null || String(v).trim() === "") return null;
    const n = Number(v);
    return Number.isFinite(n) && n > 0 ? n : null;
  };

  type EducationTargetPayload = {
    name_of_kid: string;
    ug_target_amount?: number | null;
    pg_target_amount?: number | null;
  };

  const postPlanRun = async (
    overrides?: PlanOverrides | null,
    educationTargetsPayload?: EducationTargetPayload[],
  ): Promise<PlanResponse> => {
    const payload: {
      record_id: string;
      overrides?: PlanOverrides;
      education_targets?: EducationTargetPayload[];
    } = {
      record_id: recordId!,
    };
    if (overrides && Object.keys(overrides).length > 0) {
      payload.overrides = overrides;
    }
    if (educationTargetsPayload?.length) {
      payload.education_targets = educationTargetsPayload;
    }
    const res = await fetch("/api/financial-plan/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = (await res.json()) as PlanResponse;
    if (!res.ok) {
      const msg =
        typeof data.detail === "string" ? data.detail : "Plan run failed";
      throw new Error(msg);
    }
    return data;
  };

  const runPlan = async (educationTargetsPayload?: EducationTargetPayload[]) => {
    if (!recordId) return;
    setLoading(true);
    setError(null);
    setStatus({ msg: "Generating financial plan…", type: "info" });
    try {
      const isFirstRun = planTabs.length === 0;
      const hasEdits = Boolean(
        planOverrides && Object.keys(planOverrides).length > 0,
      );

      if (isFirstRun) {
        // Intentional two-run on first edit: Original (Airtable) always runs first;
        // if rates were edited, a second pass with overrides creates Plan 2 (~1–3 min extra).
        setStatus({
          msg: "Generating original plan (Airtable baseline)…",
          type: "info",
        });
        const baseline = await postPlanRun(null, educationTargetsPayload);
        if (baseline.summary) {
          onPlanComplete({
            overrides: null,
            appliedRates: resolveAppliedRates(originalRates, null),
            summary: baseline.summary,
            label: "Original (Airtable)",
          });
        }

        if (hasEdits && planOverrides) {
          setStatus({
            msg: "Generating edited scenario (Plan 2)…",
            type: "info",
          });
          const edited = await postPlanRun(planOverrides, educationTargetsPayload);
          if (edited.summary) {
            onPlanComplete({
              overrides: planOverrides,
              appliedRates: resolveAppliedRates(originalRates, planOverrides),
              summary: edited.summary,
              label: "Plan 2",
            });
          }
        }
      } else {
        const runOverrides = hasEdits && planOverrides ? planOverrides : null;
        const data = await postPlanRun(runOverrides, educationTargetsPayload);
        if (data.summary) {
          onPlanComplete({
            overrides: runOverrides,
            appliedRates: resolveAppliedRates(originalRates, runOverrides),
            summary: data.summary,
          });
        }
      }

      setStatus({
        msg: "Plan ready — review below.",
        type: "success",
      });
    } catch (e) {
      const msg = (e as Error).message;
      setError(msg);
      setStatus({ msg, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  const onMakePlanClick = () => {
    if (!recordId) return;
    const blocks = educationBlocks ?? [];
    const t = educationTargets ?? {};
    const missing = blocks.some(
      (b) =>
        parseAmt(t[b.name]?.ug) == null ||
        (b.hasPg && parseAmt(t[b.name]?.pg) == null),
    );
    if (missing) {
      setShowWarning(true);
      return;
    }
    const education_targets = blocks.map((b) => ({
      name_of_kid: b.name,
      ug_target_amount: parseAmt(t[b.name]?.ug),
      pg_target_amount: b.hasPg ? parseAmt(t[b.name]?.pg) : null,
    }));
    runPlan(education_targets.length ? education_targets : undefined);
  };

  const s = planTabs.find((tab) => tab.id === activeTabId)?.summary;
  const sb = s?.spending_behavior;
  const savingPct =
    sb && typeof sb.saving_ratio === "number"
      ? sb.saving_ratio * 100
      : null;
  const expensePct =
    sb && typeof sb.expense_ratio === "number"
      ? sb.expense_ratio * 100
      : null;
  const redFlag = Boolean(sb?.red_flag);
  const liqFlag = String(s?.liquidity_flag ?? "");
  const flex = String(s?.flexibility ?? "");
  const liqOk = liqFlag.toLowerCase().includes("ok");
  const flexOk =
    flex.toLowerCase().includes("medium") ||
    flex.toLowerCase().includes("high");

  return (
    <>
      {loading ? <PlanGeneratingOverlay activeStep={overlayStep} /> : null}
      {showWarning ? <PlanWarningOverlay onClose={() => setShowWarning(false)} /> : null}

      <div className="mb-6 overflow-hidden rounded-xl border border-slate-200 bg-[#f0f4f8] shadow-sm dark:border-slate-700 dark:bg-slate-900/50">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-[#1a365d] bg-white px-5 py-4 shadow-sm dark:border-sky-800 dark:bg-slate-900">
          <div>
            <p className="text-[0.72rem] font-bold uppercase tracking-widest text-[#1a365d] dark:text-sky-300">
              Financial Plan Generator
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Strategizing wealth, maximizing opportunities · Armstrong workflow
            </p>
          </div>
          <button
            type="button"
            onClick={onMakePlanClick}
            disabled={disabled || loading || !recordId}
            className={cn(
              "inline-flex shrink-0 items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white transition",
              "bg-[#2b6cb0] hover:bg-[#2c5282] disabled:cursor-not-allowed disabled:opacity-50",
            )}
          >
            {loading ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                Generating…
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Make plan
              </>
            )}
          </button>
        </div>

        <div className="p-5 sm:p-6">
          {status ? (
            <div
              className={cn(
                "mb-4 rounded-lg px-4 py-3 text-sm font-medium",
                status.type === "info" && "bg-sky-50 text-sky-800 dark:bg-sky-950/50 dark:text-sky-200",
                status.type === "success" && "bg-emerald-50 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200",
                status.type === "error" && "bg-red-50 text-red-800 dark:bg-red-950/50 dark:text-red-300",
              )}
            >
              {status.msg}
            </div>
          ) : null}

          {error && status?.type !== "error" ? (
            <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </div>
          ) : null}

          {planTabs.length > 0 ? (
            <div className="mb-4 flex flex-wrap gap-2 border-b border-slate-200 pb-3 dark:border-slate-700">
              {planTabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => onActiveTabChange(tab.id)}
                  className={cn(
                    "rounded-lg px-3 py-1.5 text-xs font-semibold transition",
                    tab.id === activeTabId
                      ? "bg-[#1a365d] text-white dark:bg-sky-700"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700",
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          ) : null}

          {s ? (
            <div className="rounded-xl border border-slate-200/80 bg-white px-6 py-7 shadow-sm dark:border-slate-700 dark:bg-slate-900">
              <h2 className="mb-5 text-base font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Plan review
              </h2>

              {/* Financial health */}
              <div className="mb-7">
                <ReviewSectionTitle icon={Heart}>Financial health</ReviewSectionTitle>
                {redFlag ? (
                  <div className="mb-3.5 border-l-4 border-amber-500 bg-amber-50 py-2.5 pl-3.5 pr-3 text-amber-950 dark:bg-amber-950/40 dark:text-amber-100">
                    <p className="mb-1 text-[0.78rem] font-bold uppercase tracking-wide text-amber-900 dark:text-amber-300">
                      Spending ratio alert
                    </p>
                    <p className="text-[0.85rem] leading-relaxed">
                      Spending ratio exceeds recommended threshold. Consider
                      reviewing discretionary expenses.
                    </p>
                  </div>
                ) : null}
                <KvGrid
                  items={[
                    {
                      label: "Savings rate",
                      value: (
                        <span
                          className={cn(
                            savingPct != null &&
                              savingPct >= 20 &&
                              "text-emerald-700 dark:text-emerald-400",
                            savingPct != null &&
                              savingPct < 20 &&
                              savingPct >= 10 &&
                              "text-orange-700 dark:text-orange-400",
                            savingPct != null &&
                              savingPct < 10 &&
                              "text-red-700 dark:text-red-400",
                          )}
                        >
                          {savingPct != null ? `${savingPct.toFixed(1)}%` : "—"}
                        </span>
                      ),
                    },
                    {
                      label: "Expense ratio",
                      value: (
                        <span
                          className={cn(
                            expensePct != null &&
                              expensePct <= 60 &&
                              "text-emerald-700 dark:text-emerald-400",
                            expensePct != null &&
                              expensePct > 60 &&
                              expensePct <= 70 &&
                              "text-orange-700 dark:text-orange-400",
                            expensePct != null &&
                              expensePct > 70 &&
                              "text-red-700 dark:text-red-400",
                          )}
                        >
                          {expensePct != null ? `${expensePct.toFixed(1)}%` : "—"}
                        </span>
                      ),
                    },
                    {
                      label: "Liquidity",
                      value: (
                        <span
                          className={cn(
                            "inline-block rounded px-2 py-0.5 text-[0.8rem] font-semibold",
                            liqOk
                              ? "border border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-200"
                              : "border border-orange-300 bg-orange-50 text-orange-800 dark:border-orange-700 dark:bg-orange-950/50 dark:text-orange-200",
                          )}
                        >
                          {liqFlag || "—"}
                        </span>
                      ),
                    },
                    {
                      label: "Flexibility",
                      value: (
                        <span
                          className={cn(
                            "inline-block rounded px-2 py-0.5 text-[0.8rem] font-semibold",
                            flexOk
                              ? "border border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-200"
                              : "border border-orange-300 bg-orange-50 text-orange-800 dark:border-orange-700 dark:bg-orange-950/50 dark:text-orange-200",
                          )}
                        >
                          {flex || "—"}
                        </span>
                      ),
                    },
                  ]}
                />
              </div>

              {/* Risk */}
              <div className="mb-7">
                <ReviewSectionTitle icon={Activity}>Risk appetite</ReviewSectionTitle>
                <div className="rounded-lg border border-slate-200 bg-slate-50/80 p-4 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-200">
                  {(() => {
                    const ra = s.risk_appetite as Record<string, unknown> | undefined;
                    const inner = ra?.risk_appetite as
                      | { risk_appetite?: string; reason?: string }
                      | string
                      | undefined;
                    const label =
                      typeof inner === "string"
                        ? inner
                        : inner && typeof inner === "object"
                          ? inner.risk_appetite
                          : null;
                    const reason =
                      inner && typeof inner === "object" ? inner.reason : undefined;
                    return (
                      <>
                        <p className="font-semibold text-[#1a365d] dark:text-sky-300">
                          {label ?? "—"}
                        </p>
                        {reason ? (
                          <p className="mt-2 text-[0.85rem] leading-relaxed text-slate-600 dark:text-slate-400">
                            {reason}
                          </p>
                        ) : null}
                      </>
                    );
                  })()}
                </div>
              </div>

              {/* Surplus & pools */}
              <div className="mb-7">
                <ReviewSectionTitle icon={ArrowRightLeft}>
                  Surplus &amp; asset pools
                </ReviewSectionTitle>
                <KvGrid
                  items={[
                    {
                      label: "Monthly surplus",
                      value: (
                        <span className="text-emerald-800 dark:text-emerald-400">
                          {fmtInr(s.monthly_surplus ?? undefined)}
                        </span>
                      ),
                    },
                    {
                      label: "Unused monthly surplus",
                      value: fmtInr(s.final_unused_monthly_surplus ?? undefined),
                    },
                    {
                      label: "Ending liquid pool",
                      value: fmtInr(s.ending_liquid_pool ?? undefined),
                    },
                    {
                      label: "Ending monthly surplus (alloc)",
                      value: fmtInr(s.ending_monthly_surplus ?? undefined),
                    },
                  ]}
                />
              </div>

              {s.term_insurance_requirement ? (
                <div className="mb-7">
                  <ReviewSectionTitle icon={Shield}>
                    Term insurance requirement
                  </ReviewSectionTitle>
                  <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
                    <table className="w-full min-w-[320px] text-left text-sm">
                      <thead className="bg-slate-100 text-[0.72rem] font-bold uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                        <tr>
                          <th className="px-4 py-2.5">Component</th>
                          <th className="px-4 py-2.5 text-right">Amount (₹)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(s.term_insurance_requirement.breakdown ?? {}).map(
                          ([key, val]) => (
                            <tr
                              key={key}
                              className="border-b border-slate-200 dark:border-slate-700"
                            >
                              <td className="px-4 py-2.5 capitalize text-slate-700 dark:text-slate-300">
                                {key.replace(/_/g, " ")}
                              </td>
                              <td className="px-4 py-2.5 text-right font-medium text-slate-900 dark:text-slate-100">
                                {fmtInr(Math.abs(Number(val)))}
                                {Number(val) < 0 ? " (deduction)" : ""}
                              </td>
                            </tr>
                          ),
                        )}
                        <tr className="bg-slate-50 font-semibold dark:bg-slate-800/80">
                          <td className="px-4 py-2.5 text-slate-900 dark:text-slate-100">
                            Total cover required
                          </td>
                          <td className="px-4 py-2.5 text-right text-slate-900 dark:text-slate-100">
                            {fmtInr(s.term_insurance_requirement.total_cover_required)}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  {s.term_insurance_requirement.note ? (
                    <p className="mt-2.5 text-[0.82rem] leading-relaxed text-slate-600 dark:text-slate-400">
                      {s.term_insurance_requirement.note}
                    </p>
                  ) : null}
                </div>
              ) : null}

              {s.wealth_at_retirement_preview &&
              (s.wealth_at_retirement_preview.rows?.length ?? 0) > 0 ? (
                <div className="mb-7">
                  <ReviewSectionTitle icon={PiggyBank}>
                    Wealth at retirement
                    {s.wealth_at_retirement_preview.retirement_year
                      ? ` (${s.wealth_at_retirement_preview.retirement_year})`
                      : ""}
                  </ReviewSectionTitle>
                  <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                    {/* Left half: donut chart */}
                    <div className="min-w-0">
                      <PieChart
                        data={(s.wealth_at_retirement_preview.rows ?? [])
                          .filter((r) => Number(r.future_value) > 0)
                          .map((r) => ({
                            label: r.label || r.key || "—",
                            value: Number(r.future_value ?? 0),
                          }))}
                      />
                    </div>
                    {/* Right half: asset / corpus table */}
                    <div className="min-w-0 overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
                      <table className="w-full min-w-[260px] border-collapse text-left text-[0.83rem]">
                        <thead className="bg-slate-100 text-[0.72rem] font-bold uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                          <tr>
                            <th className="px-3.5 py-2.5">Asset</th>
                            <th className="px-3.5 py-2.5 text-right">Corpus created</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(s.wealth_at_retirement_preview.rows ?? []).map((r, i) => (
                            <tr
                              key={r.key ?? i}
                              className="border-b border-slate-200 dark:border-slate-700"
                            >
                              <td className="px-3.5 py-2.5 text-slate-700 dark:text-slate-300">
                                {r.label || r.key}
                                {r.rate && r.rate !== "-" ? (
                                  <span className="ml-1.5 text-[0.72rem] text-slate-400 dark:text-slate-500">
                                    @ {r.rate}
                                  </span>
                                ) : null}
                              </td>
                              <td className="px-3.5 py-2.5 text-right font-medium text-slate-900 dark:text-slate-100">
                                {fmtInr(r.future_value)}
                              </td>
                            </tr>
                          ))}
                          <tr className="bg-slate-50 font-semibold dark:bg-slate-800/80">
                            <td className="px-3.5 py-2.5 text-slate-900 dark:text-slate-100">
                              Total corpus
                            </td>
                            <td className="px-3.5 py-2.5 text-right text-slate-900 dark:text-slate-100">
                              {fmtInr(s.wealth_at_retirement_preview.total_corpus)}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Goal allocations — cards like reference HTML */}
              {s.goal_allocation_preview && s.goal_allocation_preview.length > 0 ? (
                <div className="mb-7">
                  <ReviewSectionTitle icon={Target}>
                    Goal allocations
                  </ReviewSectionTitle>
                  <div className="space-y-4">
                    {s.goal_allocation_preview.map((g, idx) => {
                      const status = deriveGoalStatus(g);
                      const gap = Number(g.corpus_gap ?? 0);
                      const partial = status === "partial_funded" || gap > 0;
                      return (
                        <div
                          key={`${g.goal_name}-${idx}`}
                          className={cn(
                            "rounded-lg border bg-slate-50 p-3.5 sm:p-4 dark:bg-slate-800/50",
                            partial
                              ? "border-amber-300 dark:border-amber-700"
                              : "border-slate-200 dark:border-slate-700",
                          )}
                        >
                          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                            <strong className="text-[0.95rem] text-slate-900 dark:text-slate-100">
                              {g.goal_name}
                            </strong>
                            <span
                              className={cn(
                                "inline-block rounded-xl px-2.5 py-0.5 text-[0.75rem] font-bold uppercase",
                                status === "funded" &&
                                  "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200",
                                status === "partial_funded" &&
                                  "bg-amber-50 text-amber-900 dark:bg-amber-950/50 dark:text-amber-200",
                                status === "not_funded" &&
                                  "bg-red-50 text-red-800 dark:bg-red-950/50 dark:text-red-300",
                              )}
                            >
                              {status.replaceAll("_", " ")}
                            </span>
                          </div>
                          <div className="mb-2.5 text-[0.82rem] text-slate-500 dark:text-slate-400">
                            {g.start_year != null && g.end_year != null ? (
                              <>
                                Starts{" "}
                                <strong className="text-slate-800 dark:text-slate-200">
                                  {g.start_year}
                                </strong>
                                {" · "}
                                Ends{" "}
                                <strong className="text-slate-800 dark:text-slate-200">
                                  {g.end_year}
                                </strong>
                              </>
                            ) : (
                              <>
                                Target year:{" "}
                                <strong className="text-slate-800 dark:text-slate-200">
                                  {g.target_year ?? "—"}
                                </strong>
                              </>
                            )}
                            {" · "}
                            Target corpus:{" "}
                            <strong className="text-slate-800 dark:text-slate-200">
                              {fmtInr(g.target_corpus)}
                            </strong>
                            {partial && gap > 0 ? (
                              <>
                                {" · "}
                                Corpus gap:{" "}
                                <strong className="text-orange-800 dark:text-orange-400">
                                  {fmtInr(gap)}
                                </strong>
                              </>
                            ) : null}
                          </div>
                          {g.funded_from_preview && g.funded_from_preview.length > 0 ? (
                            <div className="mt-2">
                              <FundingTable rows={g.funded_from_preview} />
                            </div>
                          ) : null}
                          {(status === "partial_funded" ||
                            status === "not_funded") &&
                          (g.notes?.length || gap > 0) ? (
                            <div className="mt-3 border-l-4 border-amber-500 bg-amber-50 py-2.5 pl-3 pr-2 text-amber-950 dark:bg-amber-950/40 dark:text-amber-100">
                              <p className="mb-1 text-[0.78rem] font-bold uppercase tracking-wide text-amber-900 dark:text-amber-300">
                                Action required
                              </p>
                              <div className="text-[0.85rem] leading-relaxed">
                                {g.notes?.length ? (
                                  <ul className="list-inside list-disc space-y-1">
                                    {g.notes.map((n, j) => (
                                      <li key={j}>{n}</li>
                                    ))}
                                  </ul>
                                ) : (
                                  <p>
                                    Corpus gap of {fmtInr(gap)} remains for this
                                    goal.
                                  </p>
                                )}
                              </div>
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              {s.ssy_summary_preview && s.ssy_summary_preview.length > 0 ? (
                <SsyTrackerSection rows={s.ssy_summary_preview} />
              ) : null}

              {/* Prioritized goals table */}
              {s.sorted_goals_preview && s.sorted_goals_preview.length > 0 ? (
                <div className="mb-7">
                  <ReviewSectionTitle icon={Landmark}>
                    Prioritized goals
                  </ReviewSectionTitle>
                  <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
                    <table className="min-w-full border-collapse text-[0.83rem]">
                      <thead>
                        <tr className="border-b-2 border-slate-200 bg-slate-100 text-left text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400">
                          <th className="px-2.5 py-1.5 font-semibold">Goal</th>
                          <th className="px-2.5 py-1.5 font-semibold">Score</th>
                          <th className="px-2.5 py-1.5 font-semibold">Year</th>
                          <th className="px-2.5 py-1.5 font-semibold">Corpus</th>
                        </tr>
                      </thead>
                      <tbody>
                        {s.sorted_goals_preview.map((row, i) => (
                          <tr
                            key={i}
                            className="border-b border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/50"
                          >
                            <td className="px-2.5 py-1.5 text-slate-800 dark:text-slate-200">
                              {row.goal_name}
                            </td>
                            <td className="px-2.5 py-1.5">
                              {row.priority_score ?? "—"}
                            </td>
                            <td className="px-2.5 py-1.5">
                              {row.target_year ?? "—"}
                            </td>
                            <td className="px-2.5 py-1.5">
                              {fmtInr(row.corpus_needed)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : null}

            </div>
          ) : null}
        </div>
      </div>
    </>
  );
}
