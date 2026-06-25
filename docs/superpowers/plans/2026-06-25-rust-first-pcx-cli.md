# Rust-First PCX CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `pcx update` work from published npm/PyPI/source installs while moving the command path to Rust first.

**Architecture:** Add update install-mode detection and command planning to `pcx-rs`, then make npm/Python launchers prefer Rust when available. Keep existing source-checkout update scripts as fallback for git installs.

**Tech Stack:** Rust 2021 (`clap`, `serde_json` already present), Python stdlib launchers, Node stdlib shim, existing unittest/cargo tests.

---

## File Structure

- `tools/pe-parser/src/bin/pcx-rs.rs`: Rust CLI command dispatch plus new `update` command implementation.
- `tools/pe-parser/tests/cli.rs`: Rust integration tests for update planning/check behavior.
- `npm/bin/pcx.js`: prefer packaged Rust binary before Python fallback.
- `tools/pcx.py`: delegate `update` to Rust when `pcx-rs` exists; keep script fallback.
- `package.json`: include Rust binary path if needed by npm packaging.
- `pyproject.toml`: include Rust binary path if needed by wheel packaging.
- `README.md`: document `pcx update` install modes.

---

### Task 1: Add Rust update planning tests

**Files:**
- Modify: `tools/pe-parser/tests/cli.rs`

- [ ] **Step 1: Write failing tests**

Add tests that call `pcx-rs update --plan-json` with explicit env overrides so no package manager runs:

```rust
#[test]
fn update_plan_reports_npm_install_command() {
    let output = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["update", "--plan-json"])
        .env("PCX_UPDATE_MODE", "npm")
        .output()
        .expect("run pcx-rs update plan");
    assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    let json: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(json["mode"], "npm");
    assert_eq!(json["command"][0], "npm");
    assert_eq!(json["command"][1], "install");
    assert_eq!(json["command"][2], "-g");
    assert_eq!(json["command"][3], "pcx-ai-toolkit@latest");
}

#[test]
fn update_plan_reports_pypi_install_command() {
    let output = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["update", "--plan-json"])
        .env("PCX_UPDATE_MODE", "pypi")
        .env("PCX_PYTHON", "python-test")
        .output()
        .expect("run pcx-rs update plan");
    assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    let json: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(json["mode"], "pypi");
    assert_eq!(json["command"], serde_json::json!(["python-test", "-m", "pip", "install", "--upgrade", "pcx-ai-toolkit"]));
}
```

- [ ] **Step 2: Run tests to verify failure**

Run: `cargo test --manifest-path tools/pe-parser/Cargo.toml update_plan --test cli`

Expected: FAIL because `pcx-rs` does not recognize `update --plan-json`.

---

### Task 2: Implement Rust `update --plan-json`

**Files:**
- Modify: `tools/pe-parser/src/bin/pcx-rs.rs`

- [ ] **Step 1: Add minimal mode and plan helpers**

Add near existing command helpers:

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
enum UpdateMode {
    Source,
    Npm,
    Pypi,
    Unknown,
}

fn update_mode(repo_root: &Path) -> UpdateMode {
    match std::env::var("PCX_UPDATE_MODE").ok().as_deref() {
        Some("source") => return UpdateMode::Source,
        Some("npm") => return UpdateMode::Npm,
        Some("pypi") => return UpdateMode::Pypi,
        Some(_) => return UpdateMode::Unknown,
        None => {}
    }
    if (repo_root.join(".git")).exists() {
        UpdateMode::Source
    } else if std::env::var("npm_config_global").is_ok() || std::env::var("npm_execpath").is_ok() {
        UpdateMode::Npm
    } else if std::env::var("VIRTUAL_ENV").is_ok() || std::env::var("PIPX_HOME").is_ok() {
        UpdateMode::Pypi
    } else {
        UpdateMode::Unknown
    }
}

fn update_command(mode: &UpdateMode, repo_root: &Path, args: &[String]) -> Option<Vec<String>> {
    match mode {
        UpdateMode::Source => Some({
            let script = if cfg!(windows) { "tools/update-toolkit.ps1" } else { "tools/update-toolkit.sh" };
            let mut cmd = if cfg!(windows) {
                vec!["powershell".to_string(), "-ExecutionPolicy".to_string(), "Bypass".to_string(), "-File".to_string(), repo_root.join(script).display().to_string()]
            } else {
                vec!["bash".to_string(), repo_root.join(script).display().to_string()]
            };
            cmd.extend(args.iter().cloned());
            cmd
        }),
        UpdateMode::Npm => Some(vec!["npm".to_string(), "install".to_string(), "-g".to_string(), "pcx-ai-toolkit@latest".to_string()]),
        UpdateMode::Pypi => Some(vec![std::env::var("PCX_PYTHON").unwrap_or_else(|_| "python".to_string()), "-m".to_string(), "pip".to_string(), "install".to_string(), "--upgrade".to_string(), "pcx-ai-toolkit".to_string()]),
        UpdateMode::Unknown => None,
    }
}
```

- [ ] **Step 2: Add `cmd_update` with `--plan-json`**

```rust
fn cmd_update(repo_root: &Path, args: &[String]) -> i32 {
    let plan_json = args.iter().any(|arg| arg == "--plan-json");
    let passthrough: Vec<String> = args.iter().filter(|arg| arg.as_str() != "--plan-json").cloned().collect();
    let mode = update_mode(repo_root);
    let Some(command) = update_command(&mode, repo_root, &passthrough) else {
        eprintln!("pcx update: could not detect install mode; use npm install -g pcx-ai-toolkit@latest or python -m pip install --upgrade pcx-ai-toolkit");
        return 3;
    };
    if plan_json {
        println!("{}", serde_json::json!({
            "mode": match mode { UpdateMode::Source => "source", UpdateMode::Npm => "npm", UpdateMode::Pypi => "pypi", UpdateMode::Unknown => "unknown" },
            "command": command,
        }));
        return 0;
    }
    let mut child = Command::new(&command[0]);
    child.args(&command[1..]);
    match child.status() {
        Ok(status) => status.code().unwrap_or(3),
        Err(err) => {
            eprintln!("pcx update: failed to run {}: {}", command[0], err);
            3
        }
    }
}
```

- [ ] **Step 3: Wire dispatch**

In `main`, route `update` before Python fallback:

```rust
"update" => cmd_update(&repo_root, &args.args),
```

- [ ] **Step 4: Run tests to verify pass**

Run: `cargo test --manifest-path tools/pe-parser/Cargo.toml update_plan --test cli`

Expected: PASS.

---

### Task 3: Make npm shim Rust-first

**Files:**
- Modify: `npm/bin/pcx.js`
- Modify: `package.json`

- [ ] **Step 1: Write failing static test**

Add or extend a distribution test in `tests/test_distribution.py` that reads `npm/bin/pcx.js` and asserts it references `pcx-rs` before `tools/pcx.py`.

```python
def test_npm_shim_prefers_rust_cli():
    shim = (REPO_ROOT / "npm" / "bin" / "pcx.js").read_text(encoding="utf-8")
    assert "pcx-rs" in shim
    assert shim.index("pcx-rs") < shim.index("pcx.py")
```

- [ ] **Step 2: Run test to verify failure**

Run: `python -m pytest tests/test_distribution.py::test_npm_shim_prefers_rust_cli -q`

Expected: FAIL because current shim only runs Python.

- [ ] **Step 3: Implement minimal shim**

Update `npm/bin/pcx.js` to check packaged binary paths first:

```js
const fs = require("node:fs");
const rustName = process.platform === "win32" ? "pcx-rs.exe" : "pcx-rs";
const rustCandidates = [
  path.join(root, "tools", "bin", rustName),
  path.join(root, "tools", "pe-parser", "target", "release", rustName),
];
for (const rust of rustCandidates) {
  if (fs.existsSync(rust)) {
    const result = spawnSync(rust, args, { stdio: "inherit", env: { ...process.env, PCX_TOOLKIT_ROOT: root } });
    if (result.error) {
      console.error(`pcx: failed to run ${rust}: ${result.error.message}`);
      process.exit(3);
    }
    process.exit(result.status ?? 0);
  }
}
```

Keep existing Python fallback below.

- [ ] **Step 4: Ensure npm package includes binary directory**

Add `tools/bin/pcx-rs*` to `package.json` `files`.

- [ ] **Step 5: Run test to verify pass**

Run: `python -m pytest tests/test_distribution.py::test_npm_shim_prefers_rust_cli -q`

Expected: PASS.

---

### Task 4: Make Python launcher Rust-first for update

**Files:**
- Modify: `tools/pcx.py`
- Modify: `tests/test_update_command.py`

- [ ] **Step 1: Write failing test**

Add a unit test that creates a fake executable `tools/bin/pcx-rs`, runs `python tools/pcx.py update --plan-json`, and asserts the fake Rust binary saw `update --plan-json`.

```python
def test_python_cli_delegates_update_to_rust_when_available(self):
    repo = self._make_repo("update-toolkit.sh")
    try:
        bin_dir = repo / "tools" / "bin"
        bin_dir.mkdir()
        rust = bin_dir / ("pcx-rs.exe" if os.name == "nt" else "pcx-rs")
        rust.write_text("#!/usr/bin/env sh\nprintf '%s\n' \"$@\"\n", encoding="utf-8")
        rust.chmod(0o755)
        shutil.copy(REPO_ROOT / "tools" / "pcx.py", repo / "tools" / "pcx.py")
        (repo / "tools" / "lib").mkdir(parents=True)
        shutil.copytree(REPO_ROOT / "tools" / "lib", repo / "tools" / "lib", dirs_exist_ok=True)
        result = subprocess.run([sys.executable, "tools/pcx.py", "update", "--plan-json"], cwd=repo, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("update", result.stdout)
        self.assertIn("--plan-json", result.stdout)
    finally:
        shutil.rmtree(repo.parent)
```

Also import `os` and `sys`.

- [ ] **Step 2: Run test to verify failure**

Run: `python -m unittest tests.test_update_command.UpdateCommandTest.test_python_cli_delegates_update_to_rust_when_available`

Expected: FAIL because Python launcher runs shell update script.

- [ ] **Step 3: Implement Rust delegation**

Add helper to `tools/pcx.py`:

```python
def run_rust_cli_if_available(args: list[str]) -> int | None:
    exe = "pcx-rs.exe" if os.name == "nt" else "pcx-rs"
    candidates = [REPO_ROOT / "tools" / "bin" / exe, REPO_ROOT / "tools" / "pe-parser" / "target" / "release" / exe]
    for candidate in candidates:
        if candidate.exists():
            proc = subprocess.run([str(candidate), *args])
            return int(proc.returncode)
    return None
```

In `cmd == "update"` branch:

```python
rust_code = run_rust_cli_if_available([cmd, *sub_args])
if rust_code is not None:
    return rust_code
return run_script("update-toolkit", sub_args)
```

- [ ] **Step 4: Run test to verify pass**

Run: `python -m unittest tests.test_update_command.UpdateCommandTest.test_python_cli_delegates_update_to_rust_when_available`

Expected: PASS.

---

### Task 5: Document user update path

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add docs check**

Use existing README section around Quick Start and add `pcx update` examples under installation commands.

- [ ] **Step 2: Manual read check**

Run: `python -m pytest tests/test_distribution.py -q`

Expected: PASS, unless existing tests unrelated fail.

---

### Task 6: Final verification

**Files:**
- No production edits.

- [ ] **Step 1: Run focused Python tests**

Run: `python -m pytest tests/test_update_command.py tests/test_distribution.py -q`

Expected: PASS.

- [ ] **Step 2: Run focused Rust tests**

Run: `cargo test --manifest-path tools/pe-parser/Cargo.toml update_plan --test cli`

Expected: PASS.

- [ ] **Step 3: Smoke commands**

Run:

```bash
python tools/pcx.py update --plan-json
cargo run --manifest-path tools/pe-parser/Cargo.toml --bin pcx-rs -- update --plan-json
```

Expected: both print JSON plan or precise install-mode error; neither crashes.
