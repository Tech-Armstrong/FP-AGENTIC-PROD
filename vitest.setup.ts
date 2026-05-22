import "@testing-library/jest-dom/vitest";
import "./app/globals.css";
import { vi } from "vitest";

/** Recharts ResponsiveContainer needs non-zero layout in jsdom. */
Element.prototype.getBoundingClientRect = function getBoundingClientRect() {
  const width = 400;
  const height = 240;
  return {
    width,
    height,
    top: 0,
    left: 0,
    right: width,
    bottom: height,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  } as DOMRect;
};

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
