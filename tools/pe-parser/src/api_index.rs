use serde::Serialize;
use serde_json::Value;
use std::collections::{BTreeSet, HashSet};
use std::fs;
use std::path::Path;

#[derive(Serialize, Clone)]
pub struct SignatureOut {
    pub text: String,
    pub language: String,
    pub kind: String,
    pub source: String,
    pub arity: u64,
}

#[derive(Serialize, Clone)]
pub struct LookupResult {
    pub symbol: String,
    pub language: String,
    pub found: bool,
    #[serde(rename = "type")]
    pub is_type: bool,
    pub languages: Vec<String>,
    pub signatures: Vec<SignatureOut>,
    pub suggestions: Vec<String>,
}

pub fn load_api_index(repo_root: &Path) -> Result<Value, String> {
    let path = repo_root.join("knowledge").join("pcx-api-index.json");
    let text = fs::read_to_string(&path).map_err(|e| format!("{}: {e}", path.display()))?;
    serde_json::from_str(&text).map_err(|e| format!("{}: {e}", path.display()))
}

fn section_map<'a>(index: &'a Value, name: &str) -> Option<&'a serde_json::Map<String, Value>> {
    index.get(name)?.as_object()
}

fn types(index: &Value) -> HashSet<String> {
    index
        .get("types")
        .and_then(|v| v.as_array())
        .into_iter()
        .flatten()
        .filter_map(|v| v.as_str().map(|s| s.to_string()))
        .collect()
}

fn all_symbol_names(index: &Value) -> BTreeSet<String> {
    let mut out = BTreeSet::new();
    for section in ["functions", "methods"] {
        if let Some(map) = section_map(index, section) {
            out.extend(map.keys().cloned());
        }
    }
    out.extend(types(index));
    out
}

fn raw_signatures<'a>(index: &'a Value, symbol: &str) -> Vec<&'a Value> {
    let mut out = Vec::new();
    for section in ["functions", "methods"] {
        if let Some(items) = section_map(index, section)
            .and_then(|map| map.get(symbol))
            .and_then(|v| v.as_array())
        {
            out.extend(items);
        }
    }
    out
}

fn signature_text(sig: &Value) -> String {
    let args = sig
        .get("arg_types")
        .and_then(|v| v.as_array())
        .map(|items| {
            items
                .iter()
                .filter_map(|v| v.as_str())
                .collect::<Vec<_>>()
                .join(", ")
        })
        .unwrap_or_default();
    let ret = sig
        .get("return_type")
        .and_then(|v| v.as_str())
        .unwrap_or("void");
    let name = sig.get("name").and_then(|v| v.as_str()).unwrap_or("");
    let target = sig
        .get("parent_type")
        .and_then(|v| v.as_str())
        .filter(|v| !v.is_empty())
        .map(|parent| format!("{parent}.{name}"))
        .unwrap_or_else(|| name.to_string());
    format!("{ret} {target}({args})")
}

fn sig_to_out(sig: &Value) -> SignatureOut {
    SignatureOut {
        text: signature_text(sig),
        language: sig
            .get("language")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        kind: sig
            .get("kind")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        source: sig
            .get("source")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string(),
        arity: sig.get("arity").and_then(|v| v.as_u64()).unwrap_or(0),
    }
}

fn levenshtein(a: &str, b: &str) -> usize {
    let mut prev = (0..=b.len()).collect::<Vec<_>>();
    let mut cur = vec![0; b.len() + 1];
    for (i, ca) in a.bytes().enumerate() {
        cur[0] = i + 1;
        for (j, cb) in b.bytes().enumerate() {
            let cost = usize::from(ca != cb);
            cur[j + 1] = (prev[j + 1] + 1).min(cur[j] + 1).min(prev[j] + cost);
        }
        std::mem::swap(&mut prev, &mut cur);
    }
    prev[b.len()]
}

fn suggestions(index: &Value, symbol: &str) -> Vec<String> {
    let low = symbol.to_ascii_lowercase();
    let mut scored = all_symbol_names(index)
        .into_iter()
        .map(|name| {
            let nlow = name.to_ascii_lowercase();
            let mut score = levenshtein(&low, &nlow) * 4;
            if nlow.starts_with(&low[..low.len().min(3)]) {
                score = score.saturating_sub(4);
            }
            if nlow.contains(&low) || low.contains(&nlow) {
                score = score.saturating_sub(2);
            }
            (score, name)
        })
        .collect::<Vec<_>>();
    scored.sort_by(|a, b| a.0.cmp(&b.0).then_with(|| a.1.cmp(&b.1)));
    scored.into_iter().take(8).map(|(_, name)| name).collect()
}

pub fn lookup_symbol(index: &Value, symbol: &str, language: Option<&str>) -> LookupResult {
    let raw = raw_signatures(index, symbol);
    let signatures = raw
        .iter()
        .filter(|sig| {
            language.is_none_or(|lang| {
                sig.get("language")
                    .and_then(|v| v.as_str())
                    .is_some_and(|sig_lang| sig_lang == lang)
            })
        })
        .map(|sig| sig_to_out(sig))
        .collect::<Vec<_>>();
    let mut languages = raw
        .iter()
        .filter_map(|sig| sig.get("language").and_then(|v| v.as_str()))
        .map(|lang| lang.to_string())
        .collect::<Vec<_>>();
    languages.sort();
    languages.dedup();
    let type_match = types(index).contains(symbol);
    LookupResult {
        symbol: symbol.to_string(),
        language: language.unwrap_or("").to_string(),
        found: type_match || !signatures.is_empty(),
        is_type: type_match,
        languages,
        signatures,
        suggestions: suggestions(index, symbol),
    }
}

pub fn print_lookup_human(result: &LookupResult) {
    let language = if result.language.is_empty() {
        "any language"
    } else {
        result.language.as_str()
    };
    if !result.found {
        println!("not found: {} ({language})", result.symbol);
        if !result.suggestions.is_empty() {
            println!("near matches:");
            for item in &result.suggestions {
                println!("  - {item}");
            }
        }
        return;
    }
    println!("found: {} ({language})", result.symbol);
    if !result.languages.is_empty() {
        println!("languages: {}", result.languages.join(", "));
    }
    if result.is_type {
        println!("type: yes");
    }
    if !result.signatures.is_empty() {
        println!("signatures:");
        for sig in &result.signatures {
            println!("  - [{}] {}", sig.language, sig.text);
            println!("    source: {}", sig.source);
        }
    }
}
