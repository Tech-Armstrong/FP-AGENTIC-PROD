"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "dashboard-sidebar-collapsed";
const MOBILE_QUERY = "(max-width: 767px)";

export function useDashboardSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "true") setCollapsed(true);

    const mq = window.matchMedia(MOBILE_QUERY);
    const apply = () => {
      const mobile = mq.matches;
      setIsMobile(mobile);
      if (mobile) {
        setMobileOpen(false);
      }
    };
    apply();
    mq.addEventListener("change", apply);
    setHydrated(true);
    return () => mq.removeEventListener("change", apply);
  }, []);

  const toggleCollapsed = useCallback(() => {
    if (isMobile) {
      setMobileOpen((open) => !open);
      return;
    }
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem(STORAGE_KEY, String(next));
      return next;
    });
  }, [isMobile]);

  const closeMobile = useCallback(() => {
    setMobileOpen(false);
  }, []);

  const expandSidebar = useCallback(() => {
    if (isMobile) {
      setMobileOpen(true);
      return;
    }
    setCollapsed(false);
    localStorage.setItem(STORAGE_KEY, "false");
  }, [isMobile]);

  const railCollapsed = isMobile ? !mobileOpen : collapsed;

  return {
    hydrated,
    isMobile,
    mobileOpen,
    collapsed,
    railCollapsed,
    toggleCollapsed,
    closeMobile,
    expandSidebar,
  };
}
