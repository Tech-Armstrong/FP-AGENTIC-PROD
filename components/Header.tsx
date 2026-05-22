"use client";

import Image from "next/image";

export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
      <div className="mx-auto flex max-w-7xl items-center gap-5 px-4 py-4 sm:px-6 lg:px-8">
        <div className="shrink-0 rounded-md bg-white dark:bg-gray-900">
          <Image
            src="/armstrong-capital-logo.png"
            alt="Armstrong Capital"
            width={480}
            height={120}
            className="h-20 w-auto max-w-[min(480px,55vw)] object-contain object-left sm:h-24"
            priority
          />
        </div>
        <div className="min-w-0">
          <h1 className="text-lg font-medium text-gray-900 dark:text-gray-100 sm:text-xl">
            Client Dashboard
          </h1>
          <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
            Financial planning data with AI assistance
          </p>
        </div>
      </div>
    </header>
  );
}
