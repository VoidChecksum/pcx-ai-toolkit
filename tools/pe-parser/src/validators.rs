use crate::api_index::{load_api_index, lookup_symbol};
use serde::Serialize;
use std::{
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
fn language_for(p: &Path) -> Option<&'static str> {
    match p
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_ascii_lowercase()
        .as_str()
    {
        "em" => Some("enma"),
        "as" => Some("angelscript"),
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
fn funcs(t: &str) -> std::collections::HashSet<String> {
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
fn forbidden(lang: &str, n: &str) -> Option<&'static str> {
    match (lang, n) {
        ("enma", "register_callback") => {
            Some("AngelScript lifecycle; use register_routine(cast<int64>(fn), data)")
        }
        ("enma", "log") => Some("AngelScript logging; use println(...) in Enma"),
        ("angelscript", "register_routine") => {
            Some("Enma lifecycle; use register_callback(fn, interval, data_index)")
        }
        ("angelscript", "println") => Some("Enma logging; use log(...) in AngelScript"),
        (_, "draw_esp") => {
            Some("Invented helper; use source-backed render APIs such as draw_text/draw_rect")
        }
        (_, "lua_pcall") => Some("Lua is outside pcx-ai-toolkit scope; use Enma or AngelScript"),
        _ => None,
    }
}
pub fn symbol_check(root: &Path, target: &Path) -> Result<Vec<ValidationFinding>, String> {
    let idx = load_api_index(root)?;
    let mut scripts = Vec::new();
    collect(target, &mut scripts)?;
    let mut findings = Vec::new();
    for p in scripts {
        let lang = language_for(&p).unwrap();
        let text = clean(&fs::read_to_string(&p).map_err(|e| format!("{}: {e}", p.display()))?);
        let user = funcs(&text);
        for (n, l) in calls(&text) {
            if matches!(
                n.as_str(),
                "if" | "for" | "while" | "switch" | "return" | "cast"
            ) || user.contains(&n)
            {
                continue;
            }
            if let Some(r) = forbidden(lang, &n) {
                findings.push(ValidationFinding {
                    file: p.display().to_string(),
                    line: l,
                    kind: "wrong_language_or_unsupported",
                    symbol: n,
                    message: r.into(),
                });
                continue;
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
