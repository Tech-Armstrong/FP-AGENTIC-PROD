import { describe, expect, it } from "vitest";
import {
  formatPythonRequirementError,
  getPythonCandidates,
  isPythonVersionSupported,
  parsePythonVersion,
  resolvePython,
} from "../../scripts/resolvePython.mjs";

describe("parsePythonVersion", () => {
  it("parses plain and prefixed version strings", () => {
    expect(parsePythonVersion("3.12.1")).toEqual({ major: 3, minor: 12 });
    expect(parsePythonVersion("Python 3.9.6")).toEqual({ major: 3, minor: 9 });
  });
});

describe("isPythonVersionSupported", () => {
  it("requires Python 3.10 or newer", () => {
    expect(isPythonVersionSupported(3, 9)).toBe(false);
    expect(isPythonVersionSupported(3, 10)).toBe(true);
    expect(isPythonVersionSupported(3, 12)).toBe(true);
    expect(isPythonVersionSupported(4, 0)).toBe(true);
  });
});

describe("resolvePython", () => {
  it("prefers the first supported candidate", () => {
    const resolved = resolvePython("linux", {
      exists: () => true,
      probe: (command) => {
        if (command === "python3.12") {
          return { command, version: "3.12", text: "Python 3.12.0" };
        }
        return null;
      },
    });
    expect(resolved?.command).toBe("python3.12");
  });

  it("returns null when only Python 3.9 is available", () => {
    const resolved = resolvePython("darwin", {
      exists: () => true,
      probe: (command) => {
        if (command === "python3") {
          return { command, version: "3.9", text: "Python 3.9.6" };
        }
        return null;
      },
    });
    expect(resolved).toBeNull();
  });
});

describe("getPythonCandidates", () => {
  it("includes Homebrew paths on macOS/Linux", () => {
    const candidates = getPythonCandidates("darwin");
    expect(candidates).toContain("/opt/homebrew/bin/python3.12");
  });
});

describe("formatPythonRequirementError", () => {
  it("includes brew instructions on macOS", () => {
    expect(formatPythonRequirementError("darwin")).toContain("brew install python@3.12");
  });
});
