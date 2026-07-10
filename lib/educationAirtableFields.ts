export const EDUCATION_DESTINATION_OPTIONS = ["Domestic", "International"] as const;

export type EducationDestination = (typeof EDUCATION_DESTINATION_OPTIONS)[number];

export function educationDestinationAirtableKey(
  childSlot: number,
  side: "ug" | "pg",
): string {
  if (childSlot < 1 || childSlot > 3) {
    throw new Error(`Invalid child slot: ${childSlot}`);
  }
  const suffix =
    side === "ug" ? "graduation_destination" : "post_graduation_destination";
  return `child_${childSlot}_${suffix}`;
}

export function normalizeEducationDestination(raw: string): EducationDestination {
  const normalized = raw.trim().toLowerCase();
  if (normalized === "domestic") return "Domestic";
  if (normalized === "international") return "International";
  throw new Error(`Invalid education destination: ${raw}`);
}

export function destinationSelectValue(raw: string | null | undefined): string {
  if (!raw || raw.trim() === "") return "";
  try {
    return normalizeEducationDestination(raw);
  } catch {
    return "";
  }
}
