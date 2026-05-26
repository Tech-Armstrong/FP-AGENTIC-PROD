"use client";

export type RealEstateProperty = {
  property_name?: string;
  name?: string;
  current_value?: number | null;
  current_market_value?: number | null;
  rental_income?: number | null;
  is_self_occupied?: boolean;
};

const TH =
  "align-middle whitespace-nowrap px-4 py-2 text-[10px] font-semibold uppercase tracking-wide";
const TD = "align-middle px-4 py-2";
const ROW = "border-b border-gray-100 dark:border-gray-700";

function fmtInr(val: number | null | undefined): string {
  if (val == null || Number.isNaN(val)) return "—";
  return `₹${Number(val).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function currentValue(p: RealEstateProperty): number | null {
  const v = p.current_value ?? p.current_market_value;
  return v != null ? Number(v) : null;
}

export function RealEstateTable({ properties }: { properties: RealEstateProperty[] }) {
  const rows = (properties ?? []).filter(
    (p) => currentValue(p) != null && Number(currentValue(p)) > 0,
  );

  if (!rows.length) {
    return (
      <p className="py-4 text-center text-xs text-gray-400 dark:text-gray-500">
        No real estate information available.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className={`bg-gray-900 text-white dark:bg-gray-800 ${ROW}`}>
            <th className={`${TH} text-left`}>Property</th>
            <th className={`${TH} text-right`}>Current Value</th>
            <th className={`${TH} text-right`}>Rental Income</th>
            <th className={`${TH} text-center`}>Usage</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((p, idx) => {
            const cv = currentValue(p);
            const propName = p.property_name ?? p.name ?? `Property ${idx + 1}`;
            const rental = p.rental_income ?? 0;

            return (
              <tr
                key={`${propName}-${idx}`}
                className={`${ROW} hover:bg-blue-50/50 dark:hover:bg-gray-800/50 ${
                  idx % 2 === 0 ? "bg-white dark:bg-gray-900" : "bg-gray-50 dark:bg-gray-900/70"
                }`}
              >
                <td className={`${TD} text-left font-medium text-gray-900 dark:text-gray-100`}>
                  {propName}
                </td>
                <td className={`${TD} text-right font-semibold text-gray-900 dark:text-gray-100`}>
                  {fmtInr(cv)}
                </td>
                <td className={`${TD} text-right text-emerald-700 dark:text-emerald-400`}>
                  {rental > 0 ? `${fmtInr(rental)}/mo` : "Nil"}
                </td>
                <td className={`${TD} text-center`}>
                  {p.is_self_occupied !== false && rental <= 0 ? (
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                      Self Occupied
                    </span>
                  ) : (
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-800 dark:bg-amber-950 dark:text-amber-200">
                      Investment
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr className="bg-gray-900 font-semibold text-white dark:bg-gray-800">
            <td className={`${TD} text-left text-sm`}>Total</td>
            <td className={`${TD} text-right text-sm`}>
              {fmtInr(rows.reduce((s, p) => s + (currentValue(p) ?? 0), 0))}
            </td>
            <td className={`${TD} text-right text-sm text-emerald-300`}>
              {fmtInr(rows.reduce((s, p) => s + (p.rental_income ?? 0), 0))}/mo
            </td>
            <td className={TD} />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
