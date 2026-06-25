#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const script = path.join(root, "tools", "pcx.py");
const args = process.argv.slice(2);
const candidates = process.platform === "win32"
  ? [["py", ["-3"]], ["python", []], ["python3", []]]
  : [["python3", []], ["python", []]];

let lastError = null;
for (const [command, prefix] of candidates) {
  const result = spawnSync(command, [...prefix, script, ...args], {
    stdio: "inherit",
    env: { ...process.env, PCX_TOOLKIT_ROOT: root }
  });

  if (result.error && result.error.code === "ENOENT") {
    lastError = result.error;
    continue;
  }
  if (result.error) {
    console.error(`pcx: failed to run ${command}: ${result.error.message}`);
    process.exit(3);
  }
  process.exit(result.status ?? 0);
}

console.error("pcx: Python 3.10+ is required. Install Python, then retry.");
if (lastError) console.error(`last error: ${lastError.message}`);
process.exit(3);
