#!/usr/bin/env node
import path from "node:path";
import { fileURLToPath } from "node:url";
import { runStartDev } from "./startDevPlatform.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const exitCode = runStartDev(process.platform, repoRoot, process.argv.slice(2));
process.exit(exitCode);
