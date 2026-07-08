import path from "node:path";
import { spawnSync } from "node:child_process";

/**
 * Resolve the OS-specific command to start the full dev stack.
 * @param {NodeJS.Platform} platform
 * @param {string} repoRoot
 * @param {string[]} [argv]
 * @returns {{ executable: string; args: string[]; shell?: boolean }}
 */
export function resolveStartDevCommand(platform, repoRoot, argv = []) {
  const skipInstall = argv.some(
    (arg) =>
      arg === "--skip-install" ||
      arg === "-SkipInstall" ||
      arg === "--SkipInstall",
  );

  if (platform === "win32") {
    const args = [
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      path.join(repoRoot, "scripts", "start-dev.ps1"),
    ];
    if (skipInstall) {
      args.push("-SkipInstall");
    }
    return { executable: "powershell", args, shell: true };
  }

  const args = [path.join(repoRoot, "scripts", "start-dev.sh")];
  if (skipInstall) {
    args.push("--skip-install");
  }
  return { executable: "bash", args };
}

/**
 * Spawn the platform start-dev script and return the child status code.
 * @param {NodeJS.Platform} platform
 * @param {string} repoRoot
 * @param {string[]} [argv]
 * @param {typeof spawnSync} [spawnFn]
 * @returns {number}
 */
export function runStartDev(platform, repoRoot, argv = [], spawnFn = spawnSync) {
  const command = resolveStartDevCommand(platform, repoRoot, argv);
  const result = spawnFn(command.executable, command.args, {
    stdio: "inherit",
    shell: command.shell ?? false,
    cwd: repoRoot,
  });
  return result.status ?? 1;
}
