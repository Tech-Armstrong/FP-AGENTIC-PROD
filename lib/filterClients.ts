import type { ClientListItem } from "@/components/DashboardSidebar";

/** Case-insensitive filter by client name or record id. */
export function filterClients(
  clients: ClientListItem[],
  query: string,
): ClientListItem[] {
  const q = query.trim().toLowerCase();
  if (!q) return clients;
  return clients.filter(
    (c) =>
      c.name.toLowerCase().includes(q) ||
      c.record_id.toLowerCase().includes(q),
  );
}
