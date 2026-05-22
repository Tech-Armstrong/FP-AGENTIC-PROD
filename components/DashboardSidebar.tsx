"use client";

import { useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Menu,
  Search,
  Users,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { filterClients } from "@/lib/filterClients";
import { useDashboardSidebar } from "@/lib/useDashboardSidebar";

export interface ClientListItem {
  record_id: string;
  name: string;
}

function clientInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return (parts[0]?.slice(0, 2) ?? "?").toUpperCase();
}

function ClientRow({
  client,
  selected,
  collapsed,
  onClick,
}: {
  client: ClientListItem;
  selected: boolean;
  collapsed: boolean;
  onClick: () => void;
}) {
  if (collapsed) {
    return (
      <button
        type="button"
        title={client.name}
        onClick={onClick}
        className={cn(
          "mx-auto flex h-10 w-10 items-center justify-center rounded-lg border text-xs font-bold transition-colors",
          selected
            ? "border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-200"
            : "border-gray-100 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700",
        )}
      >
        {clientInitials(client.name)}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors",
        selected
          ? "border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-200"
          : "border-gray-100 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700",
      )}
    >
      {client.name}
    </button>
  );
}

type DashboardSidebarProps = {
  clients: ClientListItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  loadingList: boolean;
  error: string | null;
};

export function DashboardSidebar({
  clients,
  selectedId,
  onSelect,
  loadingList,
  error,
}: DashboardSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const {
    hydrated,
    isMobile,
    mobileOpen,
    railCollapsed,
    toggleCollapsed,
    closeMobile,
    expandSidebar,
  } = useDashboardSidebar();

  const filteredClients = useMemo(
    () => filterClients(clients, searchQuery),
    [clients, searchQuery],
  );

  const handleSelect = (id: string) => {
    onSelect(id);
    if (isMobile) closeMobile();
  };

  const handleSearchExpand = () => {
    if (railCollapsed) expandSidebar();
  };

  const sidebarContent = (
    <>
      <div
        className={cn(
          "flex shrink-0 items-center border-b border-gray-200 dark:border-gray-700",
          railCollapsed ? "justify-center px-1 py-2" : "justify-end px-2 py-2",
        )}
      >
        <button
          type="button"
          onClick={toggleCollapsed}
          aria-label={railCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          {railCollapsed ? (
            <ChevronRight className="h-4 w-4" aria-hidden />
          ) : (
            <ChevronLeft className="h-4 w-4" aria-hidden />
          )}
        </button>
      </div>

      {!railCollapsed && (
        <div className="shrink-0 space-y-2 border-b border-gray-200 px-3 py-3 dark:border-gray-700">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Clients
          </h2>
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
              aria-hidden
            />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search clients…"
              aria-label="Search clients"
              className="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-9 pr-8 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder:text-gray-500"
            />
            {searchQuery.trim() !== "" && (
              <button
                type="button"
                aria-label="Clear search"
                onClick={() => setSearchQuery("")}
                className="absolute right-1.5 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded text-gray-400 hover:bg-gray-200 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-200"
              >
                <X className="h-3.5 w-3.5" aria-hidden />
              </button>
            )}
          </div>
        </div>
      )}

      {railCollapsed && (
        <div className="flex shrink-0 justify-center border-b border-gray-200 py-2 dark:border-gray-700">
          <button
            type="button"
            onClick={handleSearchExpand}
            aria-label="Expand sidebar to search clients"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            <Search className="h-4 w-4" aria-hidden />
          </button>
        </div>
      )}

      <div
        className={cn(
          "flex flex-1 flex-col gap-2 overflow-y-auto p-2",
          railCollapsed && "items-center",
        )}
      >
        {railCollapsed && (
          <Users
            className="h-4 w-4 text-gray-400 dark:text-gray-500"
            aria-hidden
          />
        )}
        {loadingList && (
          <div className="flex justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-b-2 border-blue-500" />
          </div>
        )}
        {error && (
          <div
            className={cn(
              "rounded-lg border border-red-100 bg-red-50 px-2 py-2 text-xs text-red-500 dark:border-red-900 dark:bg-red-950/40",
              railCollapsed && "hidden",
            )}
          >
            {error}
            <br />
            <span className="text-gray-400">
              Is the FastAPI server running on port 8000?
            </span>
          </div>
        )}
        {!loadingList && !error && clients.length === 0 && (
          <p
            className={cn(
              "px-2 text-xs text-gray-400",
              railCollapsed && "sr-only",
            )}
          >
            No clients found.
          </p>
        )}
        {!loadingList &&
          !error &&
          clients.length > 0 &&
          filteredClients.length === 0 && (
            <p
              className={cn(
                "px-2 text-xs text-gray-400",
                railCollapsed && "sr-only",
              )}
            >
              No clients found
            </p>
          )}
        {filteredClients.map((c) => (
          <ClientRow
            key={c.record_id}
            client={c}
            selected={selectedId === c.record_id}
            collapsed={railCollapsed}
            onClick={() => handleSelect(c.record_id)}
          />
        ))}
      </div>
    </>
  );

  if (!hydrated) {
    return (
      <aside className="hidden w-56 shrink-0 md:block" aria-hidden>
        <div className="h-full min-h-[200px]" />
      </aside>
    );
  }

  return (
    <>
      {isMobile && mobileOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={closeMobile}
        />
      )}

      {isMobile && !mobileOpen && (
        <button
          type="button"
          onClick={toggleCollapsed}
          aria-label="Open clients sidebar"
          className="fixed bottom-4 left-4 z-20 inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-md hover:bg-gray-50 md:hidden dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
        >
          <Menu className="h-4 w-4" aria-hidden />
          Clients
        </button>
      )}

      <aside
        role="complementary"
        aria-label="Clients sidebar"
        className={cn(
          "flex shrink-0 flex-col overflow-hidden border-gray-200 bg-white transition-[width,transform] duration-300 ease-in-out dark:border-gray-700 dark:bg-gray-900",
          railCollapsed ? "w-14" : "w-56",
          isMobile
            ? cn(
                "fixed inset-y-0 left-0 z-40 border-r shadow-xl",
                mobileOpen ? "translate-x-0" : "-translate-x-full",
              )
            : "relative border-r",
        )}
      >
        {isMobile && mobileOpen && (
          <button
            type="button"
            onClick={closeMobile}
            aria-label="Close sidebar"
            className="absolute right-2 top-3 z-10 inline-flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        {sidebarContent}
      </aside>
    </>
  );
}
