use clap::Parser;
use pe_parser::api_index::{load_api_index, lookup_symbol, print_lookup_human};
use pe_parser::mcp_schema::all_tools;
use pe_parser::validators::{symbol_check, verify_project};
use std::io::Read;
use std::path::{Path, PathBuf};
use std::process::Command;

const NATIVE_TOOLS: &[&str] = &[
    "pe-parser",
    "api-lookup",
    "pattern-format-converter",
    "anti-debug-scanner",
    "identify-protector",
    "pe-section-analyzer",
    "analyze-vmprotect",
    "dump-strings-xor",
    "module-export-mapper",
    "sig-uniqueness-checker",
    "binary-diff-summary",
    "offset-diff",
];

#[derive(Parser)]
#[command(
    about = "Rust-first command layer for pcx-ai-toolkit",
    disable_help_subcommand = true,
    trailing_var_arg = true
)]
struct Args {
    command: Option<String>,
    #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
    args: Vec<String>,
}

fn find_repo_root() -> Result<PathBuf, String> {
    let mut starts = Vec::new();
    if let Ok(exe) = std::env::current_exe() {
        starts.push(exe);
    }
    if let Ok(cwd) = std::env::current_dir() {
        starts.push(cwd);
    }
    for start in starts {
        for dir in start.ancestors() {
            if dir.join("VERSION").exists()
                && dir.join("knowledge").join("pcx-api-index.json").exists()
            {
                return Ok(dir.to_path_buf());
            }
        }
    }
    Err("could not locate pcx-ai-toolkit repository root".to_string())
}

fn version(repo_root: &Path) -> String {
    std::fs::read_to_string(repo_root.join("VERSION"))
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|_| "unknown".to_string())
}

fn print_help(repo_root: &Path) {
    println!("pcx-ai-toolkit manager CLI v{}", version(repo_root));
    println!();
    println!("Usage: pcx <command> [args]");
    println!();
    println!("Native Rust commands:");
    println!("  version");
    println!("  api <symbol> [--lang enma|angelscript] [--json]");
    println!("  mcp-schema [--json]");
    println!("  symbol-check <path> [--json]");
    println!("  verify-project <path> [--json] [--allow-placeholders] [--allow-unverified]");
    println!("  mcp overview|api_lookup <symbol> [--lang enma|angelscript]");
    println!("  doctor");
    for tool in NATIVE_TOOLS {
        println!("  {tool} [args]");
    }
    println!();
    println!("Compatibility commands delegated to Python until ported:");
    println!("  setup, update, lint, symbol-check, check-answer, create, verify, verify-project");
    println!("  build-api-index, check-drift, check-mcp, check-matrix, counts, new");
}

fn normalize_lang(lang: Option<&str>) -> Result<Option<&str>, String> {
    match lang {
        None => Ok(None),
        Some("enma" | "em" | ".em") => Ok(Some("enma")),
        Some("angelscript" | "angel-script" | "as" | ".as") => Ok(Some("angelscript")),
        Some(other) => Err(format!(
            "unsupported --lang {other:?}; use enma or angelscript"
        )),
    }
}

fn cmd_api(repo_root: &Path, args: &[String]) -> i32 {
    let mut symbol = None;
    let mut lang = None;
    let mut json = false;
    let mut i = 0usize;
    while i < args.len() {
        match args[i].as_str() {
            "--json" => json = true,
            "--lang" => {
                i += 1;
                if i >= args.len() {
                    eprintln!("ERROR: --lang requires a value");
                    return 2;
                }
                lang = Some(args[i].as_str());
            }
            "-h" | "--help" => {
                println!("Usage: pcx api <symbol> [--lang enma|angelscript] [--json]");
                return 0;
            }
            value if value.starts_with("--lang=") => {
                lang = value.split_once('=').map(|(_, v)| v);
            }
            value if value.starts_with('-') => {
                eprintln!("ERROR: unknown option {value}");
                return 2;
            }
            value => {
                if symbol.is_some() {
                    eprintln!("ERROR: unexpected argument {value:?}");
                    return 2;
                }
                symbol = Some(value);
            }
        }
        i += 1;
    }
    let Some(symbol) = symbol else {
        eprintln!("ERROR: missing symbol");
        return 2;
    };
    let lang = match normalize_lang(lang) {
        Ok(lang) => lang,
        Err(e) => {
            eprintln!("ERROR: {e}");
            return 2;
        }
    };
    let index = match load_api_index(repo_root) {
        Ok(index) => index,
        Err(e) => {
            eprintln!("ERROR: {e}");
            return 2;
        }
    };
    let result = lookup_symbol(&index, symbol, lang);
    if json {
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
    } else {
        print_lookup_human(&result);
    }
    if result.found {
        0
    } else {
        1
    }
}

fn cmd_mcp_schema(args: &[String]) -> i32 {
    if args.iter().any(|arg| arg == "--json") {
        println!("{}", serde_json::to_string_pretty(all_tools()).unwrap());
    } else {
        for tool in all_tools() {
            let h = if tool.takes_handle { " handle" } else { "" };
            println!("{}{}", tool.name, h);
        }
    }
    0
}
fn cmd_symbol_check(repo_root: &Path, args: &[String]) -> i32 {
    let json = args.iter().any(|a| a == "--json");
    let Some(path) = args.iter().find(|a| !a.starts_with('-')) else {
        eprintln!("ERROR: missing path");
        return 2;
    };
    match symbol_check(repo_root, Path::new(path)) {
        Ok(f) => {
            if json {
                println!("{}", serde_json::to_string_pretty(&f).unwrap())
            } else if f.is_empty() {
                println!("clean: symbol-check passed")
            } else {
                for x in &f {
                    println!(
                        "{}:{}: {} {}: {}",
                        x.file, x.line, x.kind, x.symbol, x.message
                    )
                }
            }
            if f.is_empty() {
                0
            } else {
                1
            }
        }
        Err(e) => {
            eprintln!("ERROR: {e}");
            2
        }
    }
}
fn count_scripts(path: &Path) -> usize {
    if path.is_file() {
        return usize::from(matches!(
            path.extension().and_then(|e| e.to_str()),
            Some("em" | "as")
        ));
    }
    let Ok(entries) = std::fs::read_dir(path) else {
        return 0;
    };
    entries
        .filter_map(Result::ok)
        .map(|entry| count_scripts(&entry.path()))
        .sum()
}

fn cmd_verify_project(repo_root: &Path, args: &[String]) -> i32 {
    let json = args.iter().any(|a| a == "--json");
    let allow_p = args.iter().any(|a| a == "--allow-placeholders");
    let allow_u = args.iter().any(|a| a == "--allow-unverified");
    let Some(path) = args.iter().find(|a| !a.starts_with('-')) else {
        eprintln!("ERROR: missing path");
        return 2;
    };
    match verify_project(repo_root, Path::new(path), allow_p, allow_u) {
        Ok(f) => {
            if json {
                let report = serde_json::json!({
                    "ok": f.is_empty(),
                    "scripts": count_scripts(Path::new(path)),
                    "finding_count": f.len(),
                    "findings": f,
                });
                println!("{}", serde_json::to_string_pretty(&report).unwrap())
            } else if f.is_empty() {
                println!("clean: project verified")
            } else {
                for x in &f {
                    println!(
                        "{}:{}: {} {}: {}",
                        x.file, x.line, x.kind, x.symbol, x.message
                    )
                }
            }
            if f.is_empty() {
                0
            } else {
                1
            }
        }
        Err(e) => {
            eprintln!("ERROR: {e}");
            2
        }
    }
}
fn mcp_overview() -> serde_json::Value {
    serde_json::json!({
        "name": "pcx-ai-toolkit",
        "schema_tools": all_tools().len(),
        "methods": ["overview", "api_lookup", "validate_code", "validate_answer", "validate_project"],
        "authorized_use": {
            "scope": "owned-lab-ctf-or-authorized-research",
            "no_public_multiplayer_abuse": true,
            "requires_evidence": true
        }
    })
}

fn cmd_mcp(repo_root: &Path, args: &[String]) -> i32 {
    if args.is_empty() {
        let mut input = String::new();
        if let Err(err) = std::io::stdin().read_to_string(&mut input) {
            eprintln!("ERROR: failed to read stdin: {err}");
            return 2;
        }
        let req: serde_json::Value = match serde_json::from_str(&input) {
            Ok(req) => req,
            Err(err) => {
                eprintln!("ERROR: invalid JSON request: {err}");
                return 2;
            }
        };
        let id = req.get("id").cloned().unwrap_or(serde_json::Value::Null);
        let method = req.get("method").and_then(|m| m.as_str()).unwrap_or("");
        if method == "overview" {
            let result = mcp_overview();
            println!(
                "{}",
                serde_json::to_string_pretty(
                    &serde_json::json!({"jsonrpc":"2.0","id":id,"result":result})
                )
                .unwrap()
            );
            return 0;
        }
        eprintln!("ERROR: unknown MCP method {method}");
        return 2;
    }
    let Some(method) = args.first().map(|s| s.as_str()) else {
        unreachable!()
    };
    match method {
        "overview" => {
            println!("{}", serde_json::to_string_pretty(&mcp_overview()).unwrap());
            0
        }
        "api_lookup" => {
            let Some(symbol) = args.get(1).map(|s| s.as_str()) else {
                eprintln!("ERROR: missing symbol");
                return 2;
            };
            let mut lang = None;
            let mut i = 2;
            while i < args.len() {
                if args[i] == "--lang" {
                    i += 1;
                    lang = args.get(i).map(|s| s.as_str())
                }
                i += 1;
            }
            let lang = match normalize_lang(lang) {
                Ok(l) => l,
                Err(e) => {
                    eprintln!("ERROR: {e}");
                    return 2;
                }
            };
            let idx = match load_api_index(repo_root) {
                Ok(i) => i,
                Err(e) => {
                    eprintln!("ERROR: {e}");
                    return 2;
                }
            };
            println!(
                "{}",
                serde_json::to_string_pretty(&lookup_symbol(&idx, symbol, lang)).unwrap()
            );
            0
        }
        _ => {
            eprintln!("ERROR: unknown MCP method {method}");
            2
        }
    }
}

fn cmd_doctor(repo_root: &Path) -> i32 {
    let mut checks = Vec::new();
    checks.push((
        "git installed",
        Command::new("git").arg("--version").output().is_ok(),
    ));
    checks.push((
        "node installed",
        Command::new("node").arg("--version").output().is_ok(),
    ));
    checks.push((
        "cargo installed",
        Command::new("cargo").arg("--version").output().is_ok(),
    ));
    checks.push((
        "knowledge/pcx-api-index.json exists",
        repo_root
            .join("knowledge")
            .join("pcx-api-index.json")
            .exists(),
    ));
    checks.push((
        "docs/COUNTS.json exists",
        repo_root.join("docs").join("COUNTS.json").exists(),
    ));
    for tool in NATIVE_TOOLS {
        let ext = if cfg!(windows) { ".exe" } else { "" };
        checks.push((
            Box::leak(format!("native {tool} built").into_boxed_str()),
            repo_root
                .join("tools")
                .join("bin")
                .join(format!("{tool}{ext}"))
                .exists(),
        ));
    }
    println!(
        "\npcx-ai-toolkit v{} - Rust Doctor Report\n{}",
        version(repo_root),
        "-".repeat(50)
    );
    let mut failed = 0;
    for (label, ok) in &checks {
        println!("  {:<6} {}", if *ok { "[OK]" } else { "[FAIL]" }, label);
        if !ok {
            failed += 1;
        }
    }
    println!("{}", "-".repeat(50));
    if failed == 0 {
        println!("All {} checks passed.", checks.len());
        0
    } else {
        println!("{failed}/{} checks failed.", checks.len());
        1
    }
}

fn python_cmd(repo_root: &Path) -> Command {
    let python = if Command::new("python3").arg("--version").output().is_ok() {
        "python3"
    } else {
        "python"
    };
    let mut cmd = Command::new(python);
    cmd.arg(repo_root.join("tools").join("pcx.py"));
    cmd
}

fn run_python_fallback(repo_root: &Path, command: &str, args: &[String]) -> i32 {
    let status = python_cmd(repo_root).arg(command).args(args).status();
    match status {
        Ok(status) => status.code().unwrap_or(1),
        Err(e) => {
            eprintln!("ERROR: failed to run Python fallback: {e}");
            3
        }
    }
}

fn run_native_tool(repo_root: &Path, tool: &str, args: &[String]) -> Option<i32> {
    let ext = if cfg!(windows) { ".exe" } else { "" };
    let path = repo_root
        .join("tools")
        .join("bin")
        .join(format!("{tool}{ext}"));
    if !path.exists() {
        return None;
    }
    let status = Command::new(path).args(args).status().ok()?;
    Some(status.code().unwrap_or(1))
}

fn main() {
    let args = Args::parse();
    let repo_root = match find_repo_root() {
        Ok(root) => root,
        Err(e) => {
            eprintln!("ERROR: {e}");
            std::process::exit(2);
        }
    };
    let Some(command) = args.command.as_deref() else {
        print_help(&repo_root);
        return;
    };
    let command = command.to_ascii_lowercase();
    let rc = match command.as_str() {
        "help" | "-h" | "--help" => {
            print_help(&repo_root);
            0
        }
        "version" | "-v" | "--version" => {
            println!("pcx-ai-toolkit v{}", version(&repo_root));
            0
        }
        "api" | "api-lookup" => cmd_api(&repo_root, &args.args),
        "mcp" => cmd_mcp(&repo_root, &args.args),
        "mcp-schema" => cmd_mcp_schema(&args.args),
        "symbol-check" => cmd_symbol_check(&repo_root, &args.args),
        "verify-project" | "verify" => cmd_verify_project(&repo_root, &args.args),
        "doctor" => cmd_doctor(&repo_root),
        tool if NATIVE_TOOLS.contains(&tool) => run_native_tool(&repo_root, tool, &args.args)
            .unwrap_or_else(|| run_python_fallback(&repo_root, tool, &args.args)),
        other => run_python_fallback(&repo_root, other, &args.args),
    };
    std::process::exit(rc);
}
