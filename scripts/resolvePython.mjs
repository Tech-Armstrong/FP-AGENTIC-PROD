import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const MIN_PYTHON_MAJOR = 3;
export const MIN_PYTHON_MINOR = 10;

/**
 * @param {number} major
 * @param {number} minor
 */
export function isPythonVersionSupported(major, minor) {
  if (major > MIN_PYTHON_MAJOR) return true;
  if (major < MIN_PYTHON_MAJOR) return false;
  return minor >= MIN_PYTHON_MINOR;
}

/**
 * @param {string} versionText e.g. "3.9.6" or "Python 3.12.1"
 */
export function parsePythonVersion(versionText) {
  const match = versionText.match(/(\d+)\.(\d+)/);
  if (!match) return null;
  return { major: Number(match[1]), minor: Number(match[2]) };
}

/**
 * @param {string} command
 * @param {string[]} [args]
 */
export function probePython(command, args = ["--version"]) {
  const result = spawnSync(command, args, { encoding: "utf8" });
  if (result.status !== 0) return null;
  const text = `${result.stdout ?? ""}${result.stderr ?? ""}`.trim();
  const parsed = parsePythonVersion(text);
  if (!parsed || !isPythonVersionSupported(parsed.major, parsed.minor)) {
    return null;
  }
  return { command, version: `${parsed.major}.${parsed.minor}`, text };
}

/**
 * @param {NodeJS.Platform} [platform]
 * @returns {string[]}
 */
export function getPythonCandidates(platform = process.platform) {
  if (platform === "win32") {
    return [
      "py -3.13",
      "py -3.12",
      "py -3.11",
      "py -3.10",
      "python",
      "python3",
    ];
  }

  return [
    "python3.13",
    "python3.12",
    "python3.11",
    "python3.10",
    "/opt/homebrew/bin/python3.13",
    "/opt/homebrew/bin/python3.12",
    "/opt/homebrew/bin/python3.11",
    "/opt/homebrew/bin/python3.10",
    "/usr/local/bin/python3.13",
    "/usr/local/bin/python3.12",
    "/usr/local/bin/python3.11",
    "/usr/local/bin/python3.10",
    "python3",
    "python",
  ];
}

/**
 * @param {NodeJS.Platform} [platform]
 * @param {{ probe?: typeof probePython, exists?: (path: string) => boolean }} [deps]
 * @returns {{ command: string, version: string } | null}
 */
export function resolvePython(platform = process.platform, deps = {}) {
  const probe = deps.probe ?? probePython;
  const exists = deps.exists ?? ((path) => fs.existsSync(path));

  for (const candidate of getPythonCandidates(platform)) {
    if (candidate.includes(" ")) {
      const [command, ...args] = candidate.split(" ");
      const hit = probe(command, [...args, "--version"]);
      if (hit) return hit;
      continue;
    }

    if (candidate.startsWith("/") && !exists(candidate)) {
      continue;
    }

    const hit = probe(candidate);
    if (!hit) continue;

    const parsed = parsePythonVersion(hit.version ?? hit.text);
    if (parsed && isPythonVersionSupported(parsed.major, parsed.minor)) {
      return hit;
    }
  }

  return null;
}

export function formatPythonRequirementError(platform = process.platform) {
  const lines = [
    "error: Python 3.10+ is required (langchain>=1.0).",
    "Only older Python versions were found on PATH.",
  ];
  if (platform === "darwin") {
    lines.push("  brew install python@3.12");
    lines.push("  rm -rf .venv && npm run dev:all");
  } else if (platform === "win32") {
    lines.push("  Install Python 3.12 from https://www.python.org/downloads/");
    lines.push("  Then: Remove-Item -Recurse -Force .venv; npm run dev:all");
  } else {
    lines.push("  Install Python 3.10+ using your distro package manager.");
    lines.push("  rm -rf .venv && npm run dev:all");
  }
  return lines.join("\n");
}

function splitCommand(command) {
  if (!command.includes(" ")) {
    return { executable: command, prefixArgs: [] };
  }
  const [executable, ...prefixArgs] = command.split(" ");
  return { executable, prefixArgs };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const resolved = resolvePython();
  if (!resolved) {
    console.error(formatPythonRequirementError());
    process.exit(1);
  }
  process.stdout.write(resolved.command);
}
