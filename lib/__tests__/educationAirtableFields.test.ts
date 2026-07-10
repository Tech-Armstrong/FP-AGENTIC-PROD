import { describe, expect, it } from "vitest";
import {
  destinationSelectValue,
  educationDestinationAirtableKey,
  normalizeEducationDestination,
} from "@/lib/educationAirtableFields";

describe("educationAirtableFields", () => {
  it("maps child slot and side to Airtable keys", () => {
    expect(educationDestinationAirtableKey(1, "ug")).toBe("child_1_graduation_destination");
    expect(educationDestinationAirtableKey(1, "pg")).toBe(
      "child_1_post_graduation_destination",
    );
    expect(educationDestinationAirtableKey(2, "ug")).toBe("child_2_graduation_destination");
    expect(educationDestinationAirtableKey(2, "pg")).toBe(
      "child_2_post_graduation_destination",
    );
    expect(educationDestinationAirtableKey(3, "ug")).toBe("child_3_graduation_destination");
    expect(educationDestinationAirtableKey(3, "pg")).toBe(
      "child_3_post_graduation_destination",
    );
  });

  it("normalizes destination values", () => {
    expect(normalizeEducationDestination("domestic")).toBe("Domestic");
    expect(normalizeEducationDestination("INTERNATIONAL")).toBe("International");
  });

  it("returns empty select value for blank or invalid destination", () => {
    expect(destinationSelectValue("")).toBe("");
    expect(destinationSelectValue("Domestic")).toBe("Domestic");
    expect(destinationSelectValue("invalid")).toBe("");
  });
});
