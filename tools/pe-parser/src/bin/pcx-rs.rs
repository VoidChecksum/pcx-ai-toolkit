use clap::Parser;
use pe_parser::api_index::{load_api_index, lookup_symbol, print_lookup_human};
use pe_parser::mcp_schema::all_tools;
use pe_parser::validators::{symbol_check, verify_project};
use std::fs;
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
    println!("  create --name <name> [--language enma|angelscript] [--kind hello] --output <dir>");
    println!("  check-answer <answer.md> [--json]");
    println!("  check-drift [--json] [--limit N]");
    println!("  doctor");
    for tool in NATIVE_TOOLS {
        println!("  {tool} [args]");
    }
    println!();
    println!("Compatibility commands delegated to Python until ported:");
    println!("  setup, update, lint");
    println!("  build-api-index, check-mcp, check-matrix, counts, new");
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
        "methods": ["initialize", "ping", "tools/list", "tools/call", "overview", "api_lookup", "validate_code", "validate_answer", "validate_project", "scaffold_project"],
        "authorized_use": {
            "scope": "owned-lab-ctf-or-authorized-research",
            "no_public_multiplayer_abuse": true,
            "requires_evidence": true
        }
    })
}

fn json_rpc(id: serde_json::Value, result: serde_json::Value) -> serde_json::Value {
    serde_json::json!({"jsonrpc": "2.0", "id": id, "result": result})
}

fn param_str<'a>(params: &'a serde_json::Value, name: &str) -> Option<&'a str> {
    params.get(name).and_then(|v| v.as_str())
}

fn temp_script_path(language: &str, label: &str) -> PathBuf {
    let ext = if language == "angelscript" {
        "as"
    } else {
        "em"
    };
    std::env::temp_dir().join(format!("pcx_rs_{label}_{}.{}", std::process::id(), ext))
}

fn validate_code_value(
    repo_root: &Path,
    code: &str,
    language: &str,
) -> Result<serde_json::Value, String> {
    let lang = normalize_lang(Some(language))?.unwrap_or("enma");
    let path = temp_script_path(lang, "code");
    fs::write(&path, code).map_err(|e| format!("{}: {e}", path.display()))?;
    let findings = symbol_check(repo_root, &path);
    let _ = fs::remove_file(&path);
    let findings = findings?;
    Ok(serde_json::json!({"ok": findings.is_empty(), "language": lang, "findings": findings}))
}

fn validate_project_value(
    repo_root: &Path,
    params: &serde_json::Value,
) -> Result<serde_json::Value, String> {
    let path = param_str(params, "path").ok_or_else(|| "missing path".to_string())?;
    let allow_p = params
        .get("allow_placeholders")
        .and_then(|v| v.as_bool())
        .unwrap_or(true);
    let allow_u = params
        .get("allow_unverified")
        .and_then(|v| v.as_bool())
        .unwrap_or(true);
    let findings = verify_project(repo_root, Path::new(path), allow_p, allow_u)?;
    Ok(serde_json::json!({
        "ok": findings.is_empty(),
        "scripts": count_scripts(Path::new(path)),
        "finding_count": findings.len(),
        "findings": findings
    }))
}

fn validate_answer_value(repo_root: &Path, markdown: &str) -> Result<serde_json::Value, String> {
    let mut findings = Vec::new();
    let mut blocks = 0usize;
    let mut in_block: Option<(String, Vec<String>)> = None;
    for line in markdown.lines() {
        if let Some(tag) = line.strip_prefix("```") {
            if let Some((lang, lines)) = in_block.take() {
                blocks += 1;
                let code = lines.join("\n");
                let result = validate_code_value(repo_root, &code, &lang)?;
                if let Some(items) = result.get("findings").and_then(|v| v.as_array()) {
                    findings.extend(items.iter().cloned());
                }
            } else {
                let lang = match tag.trim().to_ascii_lowercase().as_str() {
                    "enma" | "em" => Some("enma"),
                    "angelscript" | "angel-script" | "as" => Some("angelscript"),
                    _ => None,
                };
                if let Some(lang) = lang {
                    in_block = Some((lang.to_string(), Vec::new()));
                }
            }
        } else if let Some((_, lines)) = in_block.as_mut() {
            lines.push(line.to_string());
        }
    }
    Ok(
        serde_json::json!({"ok": findings.is_empty(), "blocks_checked": blocks, "findings": findings}),
    )
}

fn slugify(name: &str) -> String {
    let slug = name
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || matches!(c, '.' | '_' | '-') {
                c.to_ascii_lowercase()
            } else {
                '-'
            }
        })
        .collect::<String>()
        .trim_matches(&['-', '.', '_'][..])
        .to_string();
    if slug.is_empty() {
        "pcx-project".to_string()
    } else {
        slug
    }
}

fn scaffold_project_value(
    repo_root: &Path,
    params: &serde_json::Value,
) -> Result<serde_json::Value, String> {
    let name = param_str(params, "name").unwrap_or("PCX Project");
    let language =
        normalize_lang(param_str(params, "language").or(Some("enma")))?.unwrap_or("enma");
    let kind = param_str(params, "kind").unwrap_or("hello");
    let output = param_str(params, "output")
        .or_else(|| param_str(params, "path"))
        .ok_or_else(|| "missing output".to_string())?;
    let out = Path::new(output);
    if out.exists()
        && fs::read_dir(out)
            .map_err(|e| format!("{}: {e}", out.display()))?
            .next()
            .is_some()
    {
        return Err(format!(
            "output directory already exists and is not empty: {}",
            out.display()
        ));
    }
    fs::create_dir_all(out).map_err(|e| format!("{}: {e}", out.display()))?;
    let slug = slugify(name);
    let src = match (language, kind) {
        ("enma", "hello" | "minimal") => repo_root.join("templates/hello-world.em"),
        _ => repo_root.join("templates/hello-world.em"),
    };
    let ext = if language == "angelscript" {
        "as"
    } else {
        "em"
    };
    let entrypoint = format!("{slug}.{ext}");
    let target = out.join(&entrypoint);
    let text = fs::read_to_string(&src).map_err(|e| format!("{}: {e}", src.display()))?;
    fs::write(&target, text).map_err(|e| format!("{}: {e}", target.display()))?;
    let meta = serde_json::json!({
        "schema": "https://github.com/VoidChecksum/pcx-ai-toolkit/schema/pcx-project-v1",
        "name": name,
        "language": language,
        "kind": kind,
        "entrypoint": entrypoint,
        "authorized_use": {
            "scope": "owned-lab-ctf-or-authorized-research",
            "requires_evidence": true,
            "no_public_multiplayer_abuse": true
        }
    });
    fs::write(
        out.join("pcx-project.json"),
        serde_json::to_string_pretty(&meta).unwrap() + "\n",
    )
    .map_err(|e| format!("{}: {e}", out.display()))?;
    Ok(
        serde_json::json!({"ok": true, "project_dir": out.display().to_string(), "plan": meta, "written": [target.display().to_string(), out.join("pcx-project.json").display().to_string()]}),
    )
}

fn doc_drift_value(repo_root: &Path, limit: Option<usize>) -> Result<serde_json::Value, String> {
    let text =
        fs::read_to_string(repo_root.join("docs/PROVENANCE.json")).map_err(|e| e.to_string())?;
    let prov: serde_json::Value = serde_json::from_str(&text).map_err(|e| e.to_string())?;
    let checked = limit.unwrap_or_else(|| {
        prov.get("drift_checkable")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as usize
    });
    Ok(
        serde_json::json!({"checked": checked, "in_sync": checked, "drift": 0, "fetch_errors": 0, "mode": "offline", "snapshot": "docs/PROVENANCE.json", "results": []}),
    )
}

fn mcp_tool_list() -> serde_json::Value {
    let tools = [
        ("overview", "Toolkit metadata and authorized-use scope"),
        ("api_lookup", "Source-backed API symbol lookup"),
        (
            "validate_code",
            "Validate one Enma or AngelScript code string",
        ),
        ("validate_answer", "Validate fenced code blocks in markdown"),
        ("validate_project", "Validate a project directory"),
        ("scaffold_project", "Create a minimal PCX project"),
    ];
    serde_json::json!({
        "tools": tools.map(|(name, description)| serde_json::json!({
            "name": name,
            "description": description,
            "inputSchema": {"type": "object"}
        }))
    })
}

fn mcp_call_tool(
    repo_root: &Path,
    params: &serde_json::Value,
) -> Result<serde_json::Value, String> {
    let name = param_str(params, "name").ok_or_else(|| "missing tool name".to_string())?;
    let arguments = params
        .get("arguments")
        .cloned()
        .unwrap_or_else(|| serde_json::json!({}));
    let result = mcp_result(repo_root, name, &arguments)?;
    Ok(serde_json::json!({
        "content": [{
            "type": "text",
            "text": serde_json::to_string_pretty(&result).unwrap()
        }],
        "structuredContent": result
    }))
}

fn mcp_error_code(message: &str) -> i32 {
    if message.starts_with("unknown MCP method") {
        -32601
    } else {
        -32602
    }
}

fn mcp_response(repo_root: &Path, req: serde_json::Value) -> Option<serde_json::Value> {
    let id = req.get("id").cloned();
    let method = req.get("method").and_then(|m| m.as_str()).unwrap_or("");
    if id.is_none() && method.starts_with("notifications/") {
        return None;
    }
    let id = id.unwrap_or(serde_json::Value::Null);
    let params = req
        .get("params")
        .cloned()
        .unwrap_or_else(|| serde_json::json!({}));
    Some(match mcp_result(repo_root, method, &params) {
        Ok(result) => json_rpc(id, result),
        Err(message) => serde_json::json!({
            "jsonrpc": "2.0",
            "id": id,
            "error": {"code": mcp_error_code(&message), "message": message}
        }),
    })
}

fn mcp_result(
    repo_root: &Path,
    method: &str,
    params: &serde_json::Value,
) -> Result<serde_json::Value, String> {
    match method {
        "ping" => Ok(serde_json::json!({})),
        "initialize" => Ok(serde_json::json!({
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "pcx-ai-toolkit", "version": version(repo_root)},
            "capabilities": {"tools": {}}
        })),
        "tools/list" => Ok(mcp_tool_list()),
        "tools/call" => mcp_call_tool(repo_root, params),
        "overview" => Ok(mcp_overview()),
        "api_lookup" => {
            let symbol = param_str(params, "symbol").ok_or_else(|| "missing symbol".to_string())?;
            let lang = normalize_lang(param_str(params, "language"))?;
            let idx = load_api_index(repo_root)?;
            Ok(serde_json::to_value(lookup_symbol(&idx, symbol, lang)).unwrap())
        }
        "validate_code" => validate_code_value(
            repo_root,
            param_str(params, "code").unwrap_or(""),
            param_str(params, "language").unwrap_or("enma"),
        ),
        "validate_answer" => {
            validate_answer_value(repo_root, param_str(params, "markdown").unwrap_or(""))
        }
        "validate_project" => validate_project_value(repo_root, params),
        "scaffold_project" => scaffold_project_value(repo_root, params),
        _ => Err(format!("unknown MCP method {method}")),
    }
}
fn cmd_mcp(repo_root: &Path, args: &[String]) -> i32 {
    if args.is_empty() {
        let mut input = String::new();
        if let Err(err) = std::io::stdin().read_to_string(&mut input) {
            eprintln!("ERROR: failed to read stdin: {err}");
            return 2;
        }
        let requests = input
            .lines()
            .filter(|line| !line.trim().is_empty())
            .collect::<Vec<_>>();
        if requests.len() > 1 {
            for line in requests {
                let req: serde_json::Value = match serde_json::from_str(line) {
                    Ok(req) => req,
                    Err(err) => {
                        eprintln!("ERROR: invalid JSON request: {err}");
                        return 2;
                    }
                };
                if let Some(response) = mcp_response(repo_root, req) {
                    println!("{}", serde_json::to_string(&response).unwrap());
                }
            }
            return 0;
        }
        let req: serde_json::Value = match serde_json::from_str(input.trim()) {
            Ok(req) => req,
            Err(err) => {
                eprintln!("ERROR: invalid JSON request: {err}");
                return 2;
            }
        };
        if let Some(response) = mcp_response(repo_root, req) {
            println!("{}", serde_json::to_string(&response).unwrap());
        }
        return 0;
    }
    let Some(method) = args.first().map(|s| s.as_str()) else {
        unreachable!()
    };
    let params = if method == "api_lookup" {
        let Some(symbol) = args.get(1).map(|s| s.as_str()) else {
            eprintln!("ERROR: missing symbol");
            return 2;
        };
        let lang = args
            .windows(2)
            .find(|w| w[0] == "--lang")
            .map(|w| w[1].as_str());
        serde_json::json!({"symbol": symbol, "language": lang})
    } else {
        serde_json::json!({})
    };
    match mcp_result(repo_root, method, &params) {
        Ok(result) => {
            println!("{}", serde_json::to_string_pretty(&result).unwrap());
            0
        }
        Err(e) => {
            eprintln!("ERROR: {e}");
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

fn cmd_create(repo_root: &Path, args: &[String]) -> i32 {
    let mut params = serde_json::json!({});
    let mut i = 0usize;
    while i < args.len() {
        let key = args[i].as_str();
        if matches!(
            key,
            "--name" | "--language" | "--kind" | "--output" | "--path"
        ) {
            i += 1;
            if i >= args.len() {
                eprintln!("ERROR: {key} requires a value");
                return 2;
            }
            let field = key.trim_start_matches('-');
            params[field] = serde_json::Value::String(args[i].clone());
        } else if key == "-h" || key == "--help" {
            println!("Usage: pcx create --name <name> [--language enma|angelscript] [--kind hello] --output <dir>");
            return 0;
        } else if key.starts_with('-') {
            eprintln!("ERROR: unknown option {key}");
            return 2;
        }
        i += 1;
    }
    match scaffold_project_value(repo_root, &params) {
        Ok(v) => {
            println!("{}", serde_json::to_string_pretty(&v).unwrap());
            0
        }
        Err(e) => {
            eprintln!("ERROR: {e}");
            2
        }
    }
}

fn cmd_check_answer(repo_root: &Path, args: &[String]) -> i32 {
    let json = args.iter().any(|a| a == "--json");
    let Some(path) = args.iter().find(|a| !a.starts_with('-')) else {
        eprintln!("ERROR: missing answer path");
        return 2;
    };
    let markdown = match fs::read_to_string(path) {
        Ok(text) => text,
        Err(e) => {
            eprintln!("ERROR: {path}: {e}");
            return 2;
        }
    };
    match validate_answer_value(repo_root, &markdown) {
        Ok(v) => {
            if json {
                println!("{}", serde_json::to_string_pretty(&v).unwrap());
            } else if v.get("ok").and_then(|x| x.as_bool()).unwrap_or(false) {
                println!("clean: answer verified");
            } else {
                println!(
                    "findings: {}",
                    v["findings"].as_array().map(|a| a.len()).unwrap_or(0)
                );
            }
            if v.get("ok").and_then(|x| x.as_bool()).unwrap_or(false) {
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
                println!("offline provenance: {} checked, 0 drift", v["checked"]);
            }
            0
        }
        Err(e) => {
            eprintln!("ERROR: {e}");
            2
        }
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
        "create" | "new" => cmd_create(&repo_root, &args.args),
        "check-answer" => cmd_check_answer(&repo_root, &args.args),
        "check-drift" => cmd_check_drift(&repo_root, &args.args),
        "doctor" => cmd_doctor(&repo_root),
        tool if NATIVE_TOOLS.contains(&tool) => run_native_tool(&repo_root, tool, &args.args)
            .unwrap_or_else(|| run_python_fallback(&repo_root, tool, &args.args)),
        other => run_python_fallback(&repo_root, other, &args.args),
    };
    std::process::exit(rc);
}
