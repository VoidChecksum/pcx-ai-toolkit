#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..", "..");
const exe = process.platform === "win32" ? "pcx-rs.exe" : "pcx-rs";
const candidates = [
  process.env.PCX_RS,
  path.join(root, "tools", "bin", exe),
  path.join(root, "tools", "pe-parser", "target", "release", exe),
].filter(Boolean);

for (const candidate of candidates) {
  if (!fs.existsSync(candidate)) continue;
  const result = spawnSync(candidate, process.argv.slice(2), {
    stdio: "inherit",
    env: { ...process.env, PCX_TOOLKIT_ROOT: root },
  });
  if (result.error) {
    console.error(`pcx: failed to run ${candidate}: ${result.error.message}`);
    process.exit(3);
  }
  process.exit(result.status ?? 0);
}

console.error("pcx: pcx-rs not found. Build it with: cargo build --release --manifest-path tools/pe-parser/Cargo.toml --bin pcx-rs");
process.exit(3);
