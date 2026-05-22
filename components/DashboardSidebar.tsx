"use client";

import { useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Menu,
  Search,
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
        aria-current={selected ? "true" : undefined}
        data-selected={selected ? "true" : undefined}
        onClick={onClick}
        className={cn(
          "mx-auto flex h-10 w-10 items-center justify-center rounded-[length:var(--radius-control)] text-xs font-semibold transition-all duration-200 ease-out",
          selected
            ? "bg-brand text-brand-foreground shadow-elevation-sm"
            : "border border-border bg-surface text-body hover:bg-muted",
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
      aria-current={selected ? "true" : undefined}
      data-selected={selected ? "true" : undefined}
      className={cn(
        "group w-full rounded-[length:var(--radius-control)] border border-transparent px-3 py-3.5 text-left transition-all duration-200 ease-out",
        "border-l-[3px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40",
        selected
          ? "border-l-brand bg-brand-muted shadow-elevation-sm"
          : "border-l-transparent hover:bg-muted/70",
      )}
    >
      <span className="block text-sm font-semibold text-heading">{client.name}</span>
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
          "flex shrink-0 items-center border-b border-border",
          railCollapsed ? "justify-center px-1 py-2" : "justify-between gap-2 px-3 py-2",
        )}
      >
        {!railCollapsed && (
          <h2 className="text-sm font-semibold tracking-tight text-heading">
            Clients
          </h2>
        )}
        <button
          type="button"
          onClick={toggleCollapsed}
          aria-label={railCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-[length:var(--radius-control)] border border-border bg-surface text-muted-foreground transition-colors duration-200 ease-out hover:bg-muted hover:text-heading"
        >
          {railCollapsed ? (
            <ChevronRight className="h-4 w-4" aria-hidden />
          ) : (
            <ChevronLeft className="h-4 w-4" aria-hidden />
          )}
        </button>
      </div>

      {!railCollapsed && (
        <div className="shrink-0 border-b border-border px-4 py-4">
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search clients…"
              aria-label="Search clients"
              className="w-full rounded-[length:var(--radius-control)] border border-border bg-canvas py-2.5 pl-10 pr-9 text-sm text-heading placeholder:text-muted-foreground transition-colors duration-200 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/25"
            />
            {searchQuery.trim() !== "" && (
              <button
                type="button"
                aria-label="Clear search"
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-muted hover:text-heading"
              >
                <X className="h-3.5 w-3.5" aria-hidden />
              </button>
            )}
          </div>
        </div>
      )}

      {railCollapsed && (
        <div className="flex shrink-0 justify-center border-b border-border py-2">
          <button
            type="button"
            onClick={handleSearchExpand}
            aria-label="Expand sidebar to search clients"
            className="inline-flex h-9 w-9 items-center justify-center rounded-[length:var(--radius-control)] border border-border bg-surface text-muted-foreground transition-colors duration-200 ease-out hover:bg-muted hover:text-brand"
          >
            <Search className="h-4 w-4" aria-hidden />
          </button>
        </div>
      )}

      <div
        className={cn(
          "flex flex-1 flex-col gap-1.5 overflow-y-auto p-2",
          railCollapsed && "items-center px-1",
          !railCollapsed && "px-2",
        )}
      >
        {loadingList && (
          <div className="flex justify-center py-10">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand/30 border-t-brand" />
          </div>
        )}
        {error && (
          <div
            className={cn(
              "rounded-[length:var(--radius-control)] border border-loss/20 bg-loss-muted px-3 py-2 text-xs text-loss",
              railCollapsed && "hidden",
            )}
          >
            {error}
            <br />
            <span className="text-muted-foreground">
              Is the FastAPI server running on port 8000?
            </span>
          </div>
        )}
        {!loadingList && !error && clients.length === 0 && (
          <p
            className={cn(
              "px-2 py-4 text-center text-xs text-muted-foreground",
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
                "px-2 py-4 text-center text-xs text-muted-foreground",
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
      <aside className="hidden w-64 shrink-0 md:block" aria-hidden>
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
          className="fixed inset-0 z-30 bg-heading/40 backdrop-blur-[2px] md:hidden"
          onClick={closeMobile}
        />
      )}

      {isMobile && !mobileOpen && (
        <button
          type="button"
          onClick={toggleCollapsed}
          aria-label="Open clients sidebar"
          className="fixed bottom-5 left-5 z-20 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2.5 text-sm font-medium text-heading shadow-elevation-md transition-colors duration-200 hover:bg-muted md:hidden"
        >
          <Menu className="h-4 w-4 text-brand" aria-hidden />
          Clients
        </button>
      )}

      <aside
        role="complementary"
        aria-label="Clients sidebar"
        className={cn(
          "app-chrome",
          "flex shrink-0 flex-col overflow-hidden bg-surface transition-[width,transform] duration-300 ease-out",
          railCollapsed ? "w-14" : "w-64",
          isMobile
            ? cn(
                "fixed inset-y-0 left-0 z-40 border-r border-border shadow-elevation-lg",
                mobileOpen ? "translate-x-0" : "-translate-x-full",
              )
            : "relative border-r border-border",
        )}
      >
        {isMobile && mobileOpen && (
          <button
            type="button"
            onClick={closeMobile}
            aria-label="Close sidebar"
            className="absolute right-2 top-3 z-10 inline-flex h-7 w-7 items-center justify-center rounded-[length:var(--radius-control)] text-muted-foreground transition-colors hover:bg-muted"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        {sidebarContent}
      </aside>
    </>
  );
}
