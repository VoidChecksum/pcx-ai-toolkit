#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const args = process.argv.slice(2);
const rustName = process.platform === "win32" ? "pcx-rs.exe" : "pcx-rs";
const rustCandidates = [
  path.join(root, "pcx-bin", rustName),
  path.join(root, "tools", "bin", rustName),
  path.join(root, "tools", "pe-parser", "target", "release", rustName)
];
for (const rust of rustCandidates) {
  if (fs.existsSync(rust)) {
    const result = spawnSync(rust, args, {
      stdio: "inherit",
      env: { ...process.env, PCX_TOOLKIT_ROOT: root, PCX_UPDATE_MODE: process.env.PCX_UPDATE_MODE || "npm" }
    });
    if (result.error) {
      console.error(`pcx: failed to run ${rust}: ${result.error.message}`);
      process.exit(3);
    }
    process.exit(result.status ?? 0);
  }
}

const script = path.join(root, "tools", "pcx.py");
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
