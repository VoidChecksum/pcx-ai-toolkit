use crate::api_index::{load_api_index, lookup_symbol};
use serde::Serialize;
use std::{
    collections::{HashMap, HashSet},
    fs,
    path::{Path, PathBuf},
};
#[derive(Debug, Serialize)]
pub struct ValidationFinding {
    pub file: String,
    pub line: usize,
    pub kind: &'static str,
    pub symbol: String,
    pub message: String,
}

fn unsupported_symbols(root: &Path) -> HashMap<String, String> {
    let path = root.join("knowledge/unsupported-symbols.json");
    let Ok(text) = fs::read_to_string(path) else {
        return HashMap::new();
    };
    let Ok(json) = serde_json::from_str::<serde_json::Value>(&text) else {
        return HashMap::new();
    };
    json.get("symbols")
        .and_then(|v| v.as_object())
        .map(|symbols| {
            symbols
                .iter()
                .filter_map(|(name, reason)| reason.as_str().map(|r| (name.clone(), r.to_string())))
                .collect()
        })
        .unwrap_or_default()
}
fn language_for(p: &Path) -> Option<&'static str> {
    match p
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_ascii_lowercase()
        .as_str()
    {
        "em" => Some("enma"),
        "as" => Some("unsupported"),
        _ => None,
    }
}
fn collect(p: &Path, out: &mut Vec<PathBuf>) -> Result<(), String> {
    if p.is_file() {
        if language_for(p).is_some() {
            out.push(p.to_path_buf())
        }
        return Ok(());
    }
    for e in fs::read_dir(p).map_err(|e| format!("{}: {e}", p.display()))? {
        let p = e.map_err(|e| e.to_string())?.path();
        if p.is_dir() {
            collect(&p, out)?
        } else if language_for(&p).is_some() {
            out.push(p)
        }
    }
    Ok(())
}
fn clean(t: &str) -> String {
    t.lines()
        .map(|l| l.split("//").next().unwrap_or(""))
        .collect::<Vec<_>>()
        .join("\n")
}
fn line(t: &str, o: usize) -> usize {
    t[..o.min(t.len())].bytes().filter(|b| *b == b'\n').count() + 1
}
fn funcs(t: &str) -> HashSet<String> {
    let mut out = std::collections::HashSet::new();
    for l in t.lines() {
        let l = l.trim();
        let Some(o) = l.find('(') else { continue };
        let mut w = l[..o].split_whitespace().collect::<Vec<_>>();
        if w.len() < 2 {
            continue;
        }
        let n = w.pop().unwrap();
        if matches!(
            w.last().copied(),
            Some("void" | "int" | "int64" | "bool" | "float" | "float32" | "float64" | "string")
        ) {
            out.insert(n.into());
        }
    }
    out
}
fn calls(t: &str) -> Vec<(String, usize)> {
    let b = t.as_bytes();
    let mut out = Vec::new();
    let mut i = 0;
    while i < b.len() {
        if b[i].is_ascii_alphabetic() || b[i] == b'_' {
            let s = i;
            i += 1;
            while i < b.len() && (b[i].is_ascii_alphanumeric() || b[i] == b'_') {
                i += 1
            }
            let n = &t[s..i];
            let mut j = i;
            while j < b.len() && b[j].is_ascii_whitespace() {
                j += 1
            }
            if j < b.len() && b[j] == b'(' {
                out.push((n.into(), line(t, s)))
            }
        } else {
            i += 1
        }
    }
    out
}
fn enma_missing_import(name: &str) -> Option<&'static str> {
    match name {
        "color" => Some("color"),
        "vec2" | "vec3" | "vec4" => Some("vec"),
        "quat" | "mat4" => Some("math3d"),
        "json_parse" | "json_stringify" | "json_value" | "json_object" | "json_array" => {
            Some("json")
        }
        _ => None,
    }
}

fn enma_imports(text: &str) -> HashSet<String> {
    text.lines()
        .filter_map(|line| {
            let line = line.trim();
            line.strip_prefix("import \"")
                .and_then(|rest| rest.split('"').next())
                .map(|item| item.to_string())
        })
        .collect()
}

fn push_semantic(
    findings: &mut Vec<ValidationFinding>,
    p: &Path,
    text: &str,
    offset: usize,
    symbol: impl Into<String>,
    message: impl Into<String>,
) {
    findings.push(ValidationFinding {
        file: p.display().to_string(),
        line: line(text, offset),
        kind: "semantic_error",
        symbol: symbol.into(),
        message: message.into(),
    });
}

fn enma_semantics(p: &Path, text: &str, findings: &mut Vec<ValidationFinding>) {
    let mut start = 0usize;
    while let Some(rel) = text[start..].find("map<") {
        let at = start + rel;
        let key_start = at + "map<".len();
        let Some(comma_rel) = text[key_start..].find(',') else {
            break;
        };
        let key = text[key_start..key_start + comma_rel].trim();
        if key != "string" {
            push_semantic(
                findings,
                p,
                text,
                at,
                format!("map<{key}"),
                "Enma map<K,V> uses string keys; use imap<V> for integer keys.",
            );
        }
        start = key_start + comma_rel + 1;
    }
    let mut start = 0usize;
    while let Some(rel) = text[start..].find("uint") {
        let at = start + rel;
        let rest = &text[at..];
        if !(rest.starts_with("uint8")
            || rest.starts_with("uint16")
            || rest.starts_with("uint32")
            || rest.starts_with("uint64"))
        {
            start = at + 4;
            continue;
        }
        let stmt_end = rest.find(';').unwrap_or(rest.len());
        let stmt = &rest[..stmt_end];
        if let Some(eq) = stmt.find('=') {
            let rhs = stmt[eq + 1..].trim_start();
            if rhs.starts_with('-') && !rhs.starts_with("-cast<") {
                push_semantic(
                    findings,
                    p,
                    text,
                    at,
                    "cast<uint",
                    "Enma rejects signed-to-unsigned narrowing without an explicit cast<uint...>(...).",
                );
            }
        }
        start = at + stmt_end.max(4);
    }
    if let Some(at) = text.find("return &") {
        push_semantic(
            findings,
            p,
            text,
            at,
            "return &",
            "Enma rejects escaping local addresses; return values or store owned state.",
        );
    }
    for line_text in text.lines() {
        if line_text.contains("* ") && (line_text.contains(" = &") || line_text.contains("= &")) {
            let parts: Vec<&str> = line_text.split('*').collect();
            if parts.len() >= 2 {
                let name = parts[1].split(|c: char| c == '=' || c == ';' || c.is_whitespace()).find(|x| !x.is_empty()).unwrap_or("");
                if !name.is_empty() {
                    let plus = format!("{name} = {name} +");
                    let minus = format!("{name} = {name} -");
                    if let Some(at) = text.find(&plus).or_else(|| text.find(&minus)) {
                        push_semantic(
                            findings,
                            p,
                            text,
                            at,
                            name,
                            "Enma does not support C-style pointer arithmetic; use indexed containers or host-validated offsets.",
                        );
                    }
                }
            }
        }
    }
    if let Some(at) = text.find(" = new ") {
        push_semantic(
            findings,
            p,
            text,
            at,
            "new",
            "Stack/heap mismatch: `T x = new T()` is invalid; use `T* x = new T()` or stack construction.",
        );
    }
}

fn forbidden(lang: &str, n: &str) -> Option<&'static str> {
    match (lang, n) {
        ("enma", "register_callback") => {
            Some("AngelScript lifecycle; use register_routine(cast<int64>(fn), data)")
        }
        ("enma", "log") => Some("AngelScript logging; use println(...) in Enma"),
        (_, "draw_esp") => {
            Some("Invented helper; use source-backed render APIs such as draw_text/draw_rect")
        }
        (_, "lua_pcall") => Some("Lua is outside pcx-ai-toolkit scope; use Enma"),
        _ => None,
    }
}
pub fn symbol_check(root: &Path, target: &Path) -> Result<Vec<ValidationFinding>, String> {
    let idx = load_api_index(root)?;
    let unsupported = unsupported_symbols(root);
    let mut scripts = Vec::new();
    collect(target, &mut scripts)?;
    let mut findings = Vec::new();
    for p in scripts {
        let lang = language_for(&p).unwrap();
        if lang == "unsupported" {
            findings.push(ValidationFinding {
                file: p.display().to_string(),
                line: 0,
                kind: "unsupported_language",
                symbol: ".as".to_string(),
                message: "unsupported language: .as/AngelScript is deprecated; use Enma (.em)".to_string(),
            });
            continue;
        }
        let raw = fs::read_to_string(&p).map_err(|e| format!("{}: {e}", p.display()))?;
        let text = clean(&raw);
        let user = funcs(&text);
        let imports = enma_imports(&text);
        if lang == "enma" {
            enma_semantics(&p, &text, &mut findings);
        }
        for (n, l) in calls(&text) {
            if matches!(
                n.as_str(),
                "if" | "for" | "while" | "switch" | "return" | "cast" | "catch"
            ) || user.contains(&n)
            {
                continue;
            }
            if let Some(r) = unsupported.get(&n) {
                findings.push(ValidationFinding {
                    file: p.display().to_string(),
                    line: l,
                    kind: "unsupported_symbol",
                    symbol: n.clone(),
                    message: r.clone(),
                });
                continue;
            }
            if let Some(r) = forbidden(lang, &n) {
                findings.push(ValidationFinding {
                    file: p.display().to_string(),
                    line: l,
                    kind: if matches!(n.as_str(), "draw_esp" | "lua_pcall") {
                        "unsupported_symbol"
                    } else {
                        "wrong_language_symbol"
                    },
                    symbol: n.clone(),
                    message: r.into(),
                });
                continue;
            }
            if lang == "enma" {
                if n.starts_with("fs_") && !raw.contains("PERM_FILE") {
                    findings.push(ValidationFinding {
                        file: p.display().to_string(),
                        line: l,
                        kind: "missing_permission",
                        symbol: "PERM_FILE".into(),
                        message: format!("{n} requires PERM_FILE in the script permission set"),
                    });
                }
                if let Some(module) = enma_missing_import(&n) {
                    if !imports.contains(module) {
                        findings.push(ValidationFinding {
                            file: p.display().to_string(),
                            line: l,
                            kind: "missing_import",
                            symbol: n.clone(),
                            message: format!("import \"{module}\" before using {n}"),
                        });
                    }
                }
            }
            if !lookup_symbol(&idx, &n, Some(lang)).found {
                let any = lookup_symbol(&idx, &n, None);
                findings.push(ValidationFinding {
                    file: p.display().to_string(),
                    line: l,
                    kind: if any.found {
                        "wrong_language_symbol"
                    } else {
                        "unknown_call"
                    },
                    symbol: n.clone(),
                    message: format!("'{n}' is not source-backed for {lang}"),
                })
            }
        }
    }
    Ok(findings)
}
pub fn verify_project(
    root: &Path,
    target: &Path,
    allow_placeholders: bool,
    allow_unverified: bool,
) -> Result<Vec<ValidationFinding>, String> {
    let mut scripts = Vec::new();
    collect(target, &mut scripts)?;
    if scripts.is_empty() {
        return Err(format!("no .em or .as files found at {}", target.display()));
    }
    let mut f = symbol_check(root, target)?;
    for p in scripts {
        let text = fs::read_to_string(&p).map_err(|e| format!("{}: {e}", p.display()))?;
        for (i, l) in text.lines().enumerate() {
            let low = l.to_ascii_lowercase();
            if !allow_placeholders
                && ["placeholder", "todo", "fixme", "hack", "xxx"]
                    .iter()
                    .any(|n| low.contains(n))
            {
                f.push(ValidationFinding {
                    file: p.display().to_string(),
                    line: i + 1,
                    kind: "placeholder",
                    symbol: "placeholder".into(),
                    message: l.trim().into(),
                })
            }
            if !allow_unverified && l.to_ascii_uppercase().contains("UNVERIFIED") {
                f.push(ValidationFinding {
                    file: p.display().to_string(),
                    line: i + 1,
                    kind: "unverified",
                    symbol: "UNVERIFIED".into(),
                    message: l.trim().into(),
                })
            }
        }
    }
    Ok(f)
}
