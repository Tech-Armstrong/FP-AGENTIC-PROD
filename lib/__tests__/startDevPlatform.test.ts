import path from "node:path";
import { describe, expect, it } from "vitest";
import { resolveStartDevCommand } from "../../scripts/startDevPlatform.mjs";

const repoRoot = "/repo/chatwithyourdata";

describe("resolveStartDevCommand", () => {
  it("uses bash + start-dev.sh on macOS and Linux", () => {
    for (const platform of ["darwin", "linux"] as const) {
      const command = resolveStartDevCommand(platform, repoRoot);
      expect(command.executable).toBe("bash");
      expect(command.args).toEqual([
        path.join(repoRoot, "scripts", "start-dev.sh"),
      ]);
      expect(command.shell).toBeUndefined();
    }
  });

  it("passes --skip-install to the bash script on Unix", () => {
    const command = resolveStartDevCommand("darwin", repoRoot, [
      "--skip-install",
    ]);
    expect(command.args).toEqual([
      path.join(repoRoot, "scripts", "start-dev.sh"),
      "--skip-install",
    ]);
  });

  it("uses powershell + start-dev.ps1 on Windows", () => {
    const command = resolveStartDevCommand("win32", repoRoot);
    expect(command.executable).toBe("powershell");
    expect(command.args).toEqual([
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      path.join(repoRoot, "scripts", "start-dev.ps1"),
    ]);
    expect(command.shell).toBe(true);
  });

  it("passes -SkipInstall to the PowerShell script on Windows", () => {
    const command = resolveStartDevCommand("win32", repoRoot, ["-SkipInstall"]);
    expect(command.args).toContain("-SkipInstall");
  });

  it("accepts alternate skip-install flags on both platforms", () => {
    const unix = resolveStartDevCommand("linux", repoRoot, ["--SkipInstall"]);
    expect(unix.args).toContain("--skip-install");

    const windows = resolveStartDevCommand("win32", repoRoot, ["--skip-install"]);
    expect(windows.args).toContain("-SkipInstall");
  });
});
