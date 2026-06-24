# Rust Docs Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move provenance generation and offline doc-drift summary logic into `pcx-rs` while preserving existing Python command contracts.

**Architecture:** Add one focused Rust module, `pe_parser::docs_pipeline`, for provenance scanning, source extraction, and offline drift summaries. Wire it into `pcx-rs` via native `build-provenance` and improved `check-drift`; keep Python scripts unchanged unless a later compatibility issue appears.

**Tech Stack:** Rust 2021, `serde`, `serde_json`, stdlib filesystem/string parsing, existing Rust integration tests in `tools/pe-parser/tests/cli.rs`, existing Python unit tests.

---

## File structure

- Create: `tools/pe-parser/src/docs_pipeline.rs` — provenance model, scanners, extraction, deterministic JSON, offline drift summary.
- Modify: `tools/pe-parser/src/lib.rs` — export `docs_pipeline`.
- Modify: `tools/pe-parser/src/bin/pcx-rs.rs` — help text, `build-provenance` route, `check-drift` route, optional MCP `doc_drift_value` reuse.
- Modify: `tools/pe-parser/tests/cli.rs` — red/green CLI tests for native provenance and offline drift behavior.
- Modify only if needed after implementation: `README.md` gap row wording.

---

### Task 1: Native provenance CLI tests

**Files:**
- Modify: `tools/pe-parser/tests/cli.rs`

- [ ] **Step 1: Write failing tests**

Append these tests near `native_counts_json_does_not_need_python`:

```rust
#[test]
fn native_build_provenance_check_does_not_need_python() {
    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["build-provenance", "--check"])
        .env("PATH", "")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("PROVENANCE.json in sync"));
}

#[test]
fn native_build_provenance_json_reports_counts() {
    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["build-provenance", "--json"])
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let json: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(json["source"], "rust");
    assert!(json["count"].as_u64().unwrap() > 100);
    assert!(json["drift_checkable"].as_u64().unwrap() > 50);
    assert!(json["unmapped"].as_array().unwrap().len() > 0);
}
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cargo test --manifest-path tools/pe-parser/Cargo.toml --test cli native_build_provenance -- --nocapture
```

Expected: FAIL because `build-provenance` is unknown or still delegated through Python when `PATH` is empty.

- [ ] **Step 3: Commit red tests only**

```bash
git add tools/pe-parser/tests/cli.rs
git commit -m "test: require native provenance command"
```

---

### Task 2: Rust provenance module and command

**Files:**
- Create: `tools/pe-parser/src/docs_pipeline.rs`
- Modify: `tools/pe-parser/src/lib.rs`
- Modify: `tools/pe-parser/src/bin/pcx-rs.rs`

- [ ] **Step 1: Export module**

Add to `tools/pe-parser/src/lib.rs`:

```rust
pub mod docs_pipeline;
```

- [ ] **Step 2: Create `docs_pipeline.rs`**

Implement this module:

```rust
use serde::Serialize;
use serde_json::{Map, Value};
use std::fs;
use std::path::{Path, PathBuf};

const SKIP_DRIFT_URLS: &[&str] = &[
    "https://docs.perception.cx/perception/angel-script/cs2-extended-api.md",
    "https://docs.perception.cx/perception/angel-script/custom-draw-api.md",
    "https://docs.perception.cx/perception/enma/custom-draw-api.md",
];

#[derive(Debug, Serialize)]
pub struct ProvenanceData {
    pub generated: String,
    pub count: usize,
    pub drift_checkable: usize,
    pub unmapped: Vec<String>,
    pub files: Map<String, Value>,
}

pub fn build_provenance(repo_root: &Path) -> Result<ProvenanceData, String> {
    let docs = repo_root.join("docs");
    let mut paths = Vec::new();
    collect_markdown(&docs, &mut paths)?;
    paths.sort();

    let mut files = Map::new();
    let mut unmapped = Vec::new();

    for path in paths {
        if !is_source_doc(repo_root, &path) {
            continue;
        }
        let rel = rel(repo_root, &path)?;
        let (url, source) = extract_source(&path)?;
        let drift_check = url
            .as_deref()
            .map(|u| source == "gitbook" && !SKIP_DRIFT_URLS.contains(&u))
            .unwrap_or(false);
        if url.is_none() {
            unmapped.push(rel.clone());
        }
        files.insert(
            rel,
            serde_json::json!({"drift_check": drift_check, "source": source, "url": url}),
        );
    }

    Ok(ProvenanceData {
        generated: today_utc_date(),
        count: files.len(),
        drift_checkable: files
            .values()
            .filter(|v| v.get("drift_check").and_then(Value::as_bool) == Some(true))
            .count(),
        unmapped,
        files,
    })
}

pub fn provenance_json(repo_root: &Path) -> Result<String, String> {
    serde_json::to_string_pretty(&build_provenance(repo_root)?)
        .map(|s| format!("{s}\n"))
        .map_err(|e| e.to_string())
}

pub fn provenance_matches_committed(repo_root: &Path) -> Result<bool, String> {
    let generated: Value = serde_json::from_str(&provenance_json(repo_root)?).map_err(|e| e.to_string())?;
    let committed_path = repo_root.join("docs/PROVENANCE.json");
    let committed_text = fs::read_to_string(&committed_path)
        .map_err(|e| format!("{}: {e}", committed_path.display()))?;
    let committed: Value = serde_json::from_str(&committed_text).map_err(|e| e.to_string())?;
    Ok(strip_generated(generated) == strip_generated(committed))
}

pub fn offline_drift_summary(repo_root: &Path, limit: Option<usize>) -> Result<Value, String> {
    let text = fs::read_to_string(repo_root.join("docs/PROVENANCE.json")).map_err(|e| e.to_string())?;
    let prov: Value = serde_json::from_str(&text).map_err(|e| e.to_string())?;
    let mut targets = prov
        .get("files")
        .and_then(Value::as_object)
        .ok_or_else(|| "docs/PROVENANCE.json missing files object".to_string())?
        .iter()
        .filter(|(_, meta)| meta.get("drift_check").and_then(Value::as_bool) == Some(true))
        .collect::<Vec<_>>();
    targets.sort_by(|a, b| a.0.cmp(b.0));
    if let Some(n) = limit {
        targets.truncate(n);
    }
    let mut missing = Vec::new();
    for (rel, _) in &targets {
        if !repo_root.join(rel).exists() {
            missing.push((*rel).clone());
        }
    }
    Ok(serde_json::json!({
        "checked": targets.len(),
        "in_sync": targets.len() - missing.len(),
        "drift": 0,
        "fetch_errors": missing.len(),
        "mode": "offline",
        "snapshot": "docs/PROVENANCE.json",
        "results": missing.into_iter().map(|file| serde_json::json!({"file": file, "status": "MISSING"})).collect::<Vec<_>>()
    }))
}

fn collect_markdown(root: &Path, out: &mut Vec<PathBuf>) -> Result<(), String> {
    let entries = fs::read_dir(root).map_err(|e| format!("{}: {e}", root.display()))?;
    for entry in entries {
        let path = entry.map_err(|e| e.to_string())?.path();
        if path.is_dir() {
            collect_markdown(&path, out)?;
        } else if path.extension().and_then(|e| e.to_str()) == Some("md") {
            out.push(path);
        }
    }
    Ok(())
}

fn is_source_doc(repo_root: &Path, path: &Path) -> bool {
    if path.file_name().and_then(|n| n.to_str()) == Some("INDEX.md") {
        return false;
    }
    let Ok(rel) = path.strip_prefix(repo_root) else { return false; };
    !rel.to_string_lossy().starts_with("docs/llms-")
}

fn extract_source(path: &Path) -> Result<(Option<String>, &'static str), String> {
    let text = fs::read_to_string(path).map_err(|e| format!("{}: {e}", path.display()))?;
    let head = text.chars().take(6000).collect::<String>();
    if let Some(url) = between_after(&head, "available as [Markdown](", ")") {
        let source = classify(&url);
        return Ok((Some(url), source));
    }
    if let Some(url) = after_source_comment(&head) {
        let source = classify(&url);
        return Ok((Some(url), source));
    }
    Ok((None, "local"))
}

fn classify(url: &str) -> &'static str {
    let lower = url.to_ascii_lowercase();
    if lower.contains("gitbook.io") || lower.contains("docs.perception.cx") {
        "gitbook"
    } else if lower.contains("angelcode.com") {
        "angelcode"
    } else {
        "other"
    }
}

fn between_after(text: &str, prefix: &str, suffix: &str) -> Option<String> {
    let start = text.find(prefix)? + prefix.len();
    let end = text[start..].find(suffix)? + start;
    Some(text[start..end].trim().to_string())
}

fn after_source_comment(text: &str) -> Option<String> {
    let start = text.find("<!-- Source:")? + "<!-- Source:".len();
    let rest = text[start..].trim_start();
    let end = rest.find(char::is_whitespace).unwrap_or(rest.len());
    Some(rest[..end].trim().to_string())
}

fn rel(repo_root: &Path, path: &Path) -> Result<String, String> {
    path.strip_prefix(repo_root)
        .map(|p| p.to_string_lossy().replace('\\', "/"))
        .map_err(|e| e.to_string())
}

fn strip_generated(mut value: Value) -> Value {
    if let Some(obj) = value.as_object_mut() {
        obj.remove("generated");
    }
    value
}

fn today_utc_date() -> String {
    // ponytail: UTC date via system `date`; replace with chrono only if Windows support needs native dates.
    std::process::Command::new("date")
        .args(["-u", "+%F"])
        .output()
        .ok()
        .and_then(|out| String::from_utf8(out.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "1970-01-01".to_string())
}
```

- [ ] **Step 3: Wire `pcx-rs` imports**

Change the import block in `tools/pe-parser/src/bin/pcx-rs.rs`:

```rust
use pe_parser::docs_pipeline::{
    build_provenance, offline_drift_summary, provenance_json, provenance_matches_committed,
};
```

- [ ] **Step 4: Add native command function**

Add near `cmd_counts` / `cmd_check_drift`:

```rust
fn cmd_build_provenance(repo_root: &Path, args: &[String]) -> i32 {
    let json = args.iter().any(|a| a == "--json");
    let check = args.iter().any(|a| a == "--check");
    if check {
        match provenance_matches_committed(repo_root) {
            Ok(true) => match build_provenance(repo_root) {
                Ok(data) => {
                    if json {
                        println!(
                            "{}",
                            serde_json::to_string_pretty(&serde_json::json!({
                                "source": "rust",
                                "ok": true,
                                "count": data.count,
                                "drift_checkable": data.drift_checkable,
                                "unmapped": data.unmapped,
                            }))
                            .unwrap()
                        );
                    } else {
                        println!(
                            "PROVENANCE.json in sync ({} files, {} drift-checkable).",
                            data.count, data.drift_checkable
                        );
                    }
                    0
                }
                Err(e) => {
                    eprintln!("ERROR: {e}");
                    2
                }
            },
            Ok(false) => {
                eprintln!("PROVENANCE.json is out of sync with the source tree. Regenerate:");
                eprintln!("  pcx-rs build-provenance");
                1
            }
            Err(e) => {
                eprintln!("ERROR: {e}");
                2
            }
        }
    } else if json {
        match build_provenance(repo_root) {
            Ok(data) => {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&serde_json::json!({
                        "source": "rust",
                        "count": data.count,
                        "drift_checkable": data.drift_checkable,
                        "unmapped": data.unmapped,
                    }))
                    .unwrap()
                );
                0
            }
            Err(e) => {
                eprintln!("ERROR: {e}");
                2
            }
        }
    } else {
        match provenance_json(repo_root) {
            Ok(text) => match fs::write(repo_root.join("docs/PROVENANCE.json"), text) {
                Ok(()) => match build_provenance(repo_root) {
                    Ok(data) => {
                        println!(
                            "Wrote docs/PROVENANCE.json — {} files, {} drift-checkable, {} local-only.",
                            data.count,
                            data.drift_checkable,
                            data.unmapped.len()
                        );
                        0
                    }
                    Err(e) => {
                        eprintln!("ERROR: {e}");
                        2
                    }
                },
                Err(e) => {
                    eprintln!("ERROR: docs/PROVENANCE.json: {e}");
                    2
                }
            },
            Err(e) => {
                eprintln!("ERROR: {e}");
                2
            }
        }
    }
}
```

- [ ] **Step 5: Route command and help**

In `print_help`, add:

```rust
println!("  build-provenance [--json] [--check]");
```

Remove `build-api-index, check-mcp, check-matrix, new` line's `build-api-index` only if it would imply `build-provenance`; otherwise leave compatibility text alone.

In `main`, add route:

```rust
"build-provenance" => cmd_build_provenance(&repo_root, &args.args),
```

- [ ] **Step 6: Verify GREEN**

Run:

```bash
cargo fmt --manifest-path tools/pe-parser/Cargo.toml
cargo test --manifest-path tools/pe-parser/Cargo.toml --test cli native_build_provenance -- --nocapture
```

Expected: both provenance tests pass.

- [ ] **Step 7: Commit implementation**

```bash
git add tools/pe-parser/src/docs_pipeline.rs tools/pe-parser/src/lib.rs tools/pe-parser/src/bin/pcx-rs.rs tools/pe-parser/tests/cli.rs
git commit -m "feat: port provenance to pcx-rs"
```

---

### Task 3: Native offline drift summary parity

**Files:**
- Modify: `tools/pe-parser/tests/cli.rs`
- Modify: `tools/pe-parser/src/bin/pcx-rs.rs`
- Modify: `tools/pe-parser/src/docs_pipeline.rs`

- [ ] **Step 1: Strengthen failing/target test**

Add this test in `tools/pe-parser/tests/cli.rs`:

```rust
#[test]
fn native_check_drift_json_lists_offline_snapshot() {
    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["check-drift", "--json", "--limit", "1"])
        .env("PATH", "")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let json: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(json["mode"], "offline");
    assert_eq!(json["snapshot"], "docs/PROVENANCE.json");
    assert_eq!(json["checked"], 1);
    assert!(json["results"].as_array().unwrap().len() <= 1);
}
```

- [ ] **Step 2: Run test to verify RED or confirm gap**

Run:

```bash
cargo test --manifest-path tools/pe-parser/Cargo.toml --test cli native_check_drift_json_lists_offline_snapshot -- --nocapture
```

Expected: FAIL if current `check-drift` does not cap checked rows/results correctly or still depends on older inline JSON shape. If it passes, keep it as regression coverage and continue.

- [ ] **Step 3: Replace inline `doc_drift_value`**

In `tools/pe-parser/src/bin/pcx-rs.rs`, replace `doc_drift_value` body with:

```rust
fn doc_drift_value(repo_root: &Path, limit: Option<usize>) -> Result<serde_json::Value, String> {
    offline_drift_summary(repo_root, limit)
}
```

- [ ] **Step 4: Keep command output stable**

Keep `cmd_check_drift` shape:

```rust
fn cmd_check_drift(repo_root: &Path, args: &[String]) -> i32 {
    let json = args.iter().any(|a| a == "--json");
    let limit = args
        .windows(2)
        .find(|w| w[0] == "--limit")
        .and_then(|w| w[1].parse::<usize>().ok());
    match doc_drift_value(repo_root, limit) {
        Ok(v) => {
            if json {
                println!("{}", serde_json::to_string_pretty(&v).unwrap());
            } else {
                println!(
                    "Offline provenance check: {} tracked, {} present, {} missing.",
                    v["checked"], v["in_sync"], v["fetch_errors"]
                );
            }
            0
        }
        Err(e) => {
            eprintln!("ERROR: {e}");
            2
        }
    }
}
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cargo fmt --manifest-path tools/pe-parser/Cargo.toml
cargo test --manifest-path tools/pe-parser/Cargo.toml --test cli native_check_drift_json_lists_offline_snapshot native_create_check_answer_and_check_drift_work -- --nocapture
```

Expected: both drift-related CLI tests pass.

- [ ] **Step 6: Commit drift summary**

```bash
git add tools/pe-parser/src/docs_pipeline.rs tools/pe-parser/src/bin/pcx-rs.rs tools/pe-parser/tests/cli.rs
git commit -m "feat: port offline doc drift summary"
```

---

### Task 4: Documentation and compatibility checks

**Files:**
- Modify: `README.md`
- Modify only if behavior changed: `tools/build-provenance.py`, `tools/check-doc-drift.py`

- [ ] **Step 1: Update README gap row only after code is green**

Change the docs-pipeline gap row to say native provenance and offline drift are Rust-backed, while live fetch and API-index parsing remain future work:

```markdown
| API drift checks still rely on live Python doc scraping | The upstream docs change frequently, and live CI checks can fail from network instability | Keep native `pcx-rs build-provenance` and offline `pcx-rs check-drift` as the CI-safe path; add explicit `--live` Rust fetching and API-index parsing only if the Python scripts keep causing release failures |
```

- [ ] **Step 2: Run compatibility tests**

Run:

```bash
python3 -m unittest tests.test_doc_drift_json -v
python3 tools/build-provenance.py --check
python3 tools/check-doc-drift.py --json --limit 1
```

Expected: Python commands still pass/emit parseable JSON.

- [ ] **Step 3: Run native focused tests**

Run:

```bash
cargo test --manifest-path tools/pe-parser/Cargo.toml --test cli native_build_provenance native_check_drift_json_lists_offline_snapshot native_create_check_answer_and_check_drift_work -- --nocapture
```

Expected: all selected Rust CLI tests pass.

- [ ] **Step 4: Regenerate derived docs if counts/llms/provenance drift**

Run:

```bash
python3 tools/build-counts.py --check
python3 tools/build-llms-index.py --check
python3 tools/build-provenance.py --check
```

If any command reports drift, run the matching generator without `--check`, then re-run all three checks.

- [ ] **Step 5: Commit documentation/compatibility changes**

```bash
git add README.md docs/PROVENANCE.json docs/COUNTS.json docs/llms.txt docs/llms-full.txt docs/llms-knowledge.md docs/llms-perception-enma.md docs/llms-perception-angelscript.md tools/build-provenance.py tools/check-doc-drift.py
git commit -m "docs: update native docs pipeline status"
```

If no files changed besides README, commit only README.

---

### Task 5: Final verification and push

**Files:**
- No new edits expected.

- [ ] **Step 1: Run full focused verification**

Run:

```bash
cargo fmt --manifest-path tools/pe-parser/Cargo.toml --check
cargo test --manifest-path tools/pe-parser/Cargo.toml
python3 -m unittest tests.test_enma_docs_coverage tests.test_scenarios tests.test_symbol_check tests.test_project_workflow tests.test_doc_drift_json tests.test_distribution -v
python3 tools/verify-project.py examples/scenarios --allow-placeholders --allow-unverified
python3 tools/build-counts.py --check
python3 tools/build-llms-index.py --check
python3 tools/build-provenance.py --check
```

Expected: all commands exit `0`.

- [ ] **Step 2: Inspect final status**

Run:

```bash
git status --short
git log --oneline -5
```

Expected: no uncommitted files; newest commits are the spec/plan plus implementation slices.

- [ ] **Step 3: Push**

Run:

```bash
git push origin main
```

Expected: push succeeds.
