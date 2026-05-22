"use client";

import Image from "next/image";
import { ThemeToggle } from "./ThemeToggle";

export function Header() {
  return (
    <header className="app-chrome sticky top-0 z-20 border-b border-border/80 bg-surface/95 shadow-elevation-sm backdrop-blur-sm">
      <div className="mx-auto flex max-w-[90rem] items-center justify-between gap-6 px-5 py-3 sm:px-8 lg:px-10">
        <div className="flex min-w-0 items-center gap-5">
          <div className="shrink-0 rounded-[length:var(--radius-control)] bg-surface">
            <Image
              src="/armstrong-capital-logo.png"
              alt="Armstrong Capital"
              width={480}
              height={120}
              className="h-16 w-auto max-w-[min(400px,48vw)] object-contain object-left sm:h-[4.5rem]"
              priority
            />
          </div>
          <div className="hidden min-w-0 border-l border-border pl-5 sm:block">
            <p className="text-micro text-xs font-medium uppercase tracking-widest">
              Investor workspace
            </p>
            <h1 className="text-base font-semibold text-heading sm:text-lg">
              Client Dashboard
            </h1>
          </div>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
