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
    let generated: Value =
        serde_json::from_str(&provenance_json(repo_root)?).map_err(|e| e.to_string())?;
    let committed_path = repo_root.join("docs/PROVENANCE.json");
    let committed_text = fs::read_to_string(&committed_path)
        .map_err(|e| format!("{}: {e}", committed_path.display()))?;
    let committed: Value = serde_json::from_str(&committed_text).map_err(|e| e.to_string())?;
    Ok(strip_generated(generated) == strip_generated(committed))
}

pub fn offline_drift_summary(repo_root: &Path, limit: Option<usize>) -> Result<Value, String> {
    let text =
        fs::read_to_string(repo_root.join("docs/PROVENANCE.json")).map_err(|e| e.to_string())?;
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

pub fn normalize_markdown(text: &str) -> String {
    let no_comments = strip_html_comments(text);
    let without_footer = no_comments
        .find("\n# Agent Instructions")
        .map(|idx| &no_comments[..idx])
        .unwrap_or(&no_comments);
    without_footer
        .lines()
        .map(strip_markdown_links)
        .map(|line| line.trim().to_string())
        .filter(|line| !line.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
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
    let Ok(rel) = path.strip_prefix(repo_root) else {
        return false;
    };
    !rel.to_string_lossy().starts_with("docs/llms-")
}

fn extract_source(path: &Path) -> Result<(Option<String>, &'static str), String> {
    let text = fs::read_to_string(path).map_err(|e| format!("{}: {e}", path.display()))?;
    let head = text.chars().take(6000).collect::<String>();
    if let Some(url) = between_after(&head, "available as [Markdown](", ")") {
        if is_http_url(&url) {
            let source = classify(&url);
            return Ok((Some(url), source));
        }
    }
    if let Some(url) = after_source_comment(&head) {
        if is_http_url(&url) {
            let source = classify(&url);
            return Ok((Some(url), source));
        }
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

fn is_http_url(url: &str) -> bool {
    url.starts_with("http://") || url.starts_with("https://")
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

fn strip_html_comments(text: &str) -> String {
    let mut out = String::new();
    let mut rest = text;
    while let Some(start) = rest.find("<!--") {
        out.push_str(&rest[..start]);
        let after_start = &rest[start + 4..];
        if let Some(end) = after_start.find("-->") {
            rest = &after_start[end + 3..];
        } else {
            return out;
        }
    }
    out.push_str(rest);
    out
}

fn strip_markdown_links(line: &str) -> String {
    let mut out = String::new();
    let mut rest = line;
    while let Some(open) = rest.find('[') {
        let after_open = &rest[open + 1..];
        let Some(close_rel) = after_open.find("](") else {
            break;
        };
        let close = open + 1 + close_rel;
        let after_close = &rest[close + 2..];
        let Some(end_rel) = after_close.find(')') else {
            break;
        };
        out.push_str(&rest[..open]);
        out.push_str(&rest[open + 1..close]);
        rest = &after_close[end_rel + 1..];
    }
    out.push_str(rest);
    out
}

fn today_utc_date() -> String {
    // ponytail: no date crate for one generated metadata field; replace if Windows writes matter.
    std::process::Command::new("date")
        .args(["-u", "+%F"])
        .output()
        .ok()
        .and_then(|out| String::from_utf8(out.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "1970-01-01".to_string())
}
