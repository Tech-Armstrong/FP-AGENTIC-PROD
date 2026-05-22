import { describe, it, expect } from "vitest";
import { filterClients } from "../filterClients";

const clients = [
  { record_id: "rec1", name: "Jane Doe" },
  { record_id: "rec2", name: "John Smith" },
];

describe("filterClients", () => {
  it("returns all clients for empty query", () => {
    expect(filterClients(clients, "")).toEqual(clients);
    expect(filterClients(clients, "   ")).toEqual(clients);
  });

  it("filters case-insensitively by name", () => {
    expect(filterClients(clients, "JANE")).toHaveLength(1);
    expect(filterClients(clients, "JANE")[0].name).toBe("Jane Doe");
  });

  it("filters by record id", () => {
    expect(filterClients(clients, "rec2")).toHaveLength(1);
  });
});
