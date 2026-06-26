use serde_json::Value;
use std::collections::HashSet;
use std::fs;
use std::path::Path;

pub fn check_version_matrix(repo_root: &Path, json_out: bool, strict: bool) -> i32 {
    let changelogs_path = repo_root.join("docs").join("perception").join("changelogs.md");
    let matrix_path = repo_root.join("knowledge").join("pcx-version-matrix.md");

    if !changelogs_path.exists() || !matrix_path.exists() {
        eprintln!("ERROR: missing changelogs.md or pcx-version-matrix.md");
        return 2;
    }

    let changelogs = fs::read_to_string(&changelogs_path).unwrap_or_default();
    let matrix = fs::read_to_string(&matrix_path).unwrap_or_default();

    let header_re = regex::Regex::new(r"(?m)^##\s+([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})\s*[—\-]").unwrap();
    let api_re = regex::RegexBuilder::new(r"\b(render|proc|gui|input|cpu|zydis|unicorn|net|win|filesystem|sound|mcp|custom[- ]?draw|atomic|simd|json|regex|hash_set|sorted_map|hashmap|vec|math3d|variant|bits|scan|signature|memory|disassembl|hot[- ]?reload|world_to_screen|matrix|thread|module|pattern)\b").case_insensitive(true).build().unwrap();

    let mut mrefs = HashSet::new();
    let iso_re = regex::Regex::new(r"\d{4}-\d{2}-\d{2}").unwrap();
    for mat in iso_re.find_iter(&matrix) {
        mrefs.insert(mat.as_str().to_string());
    }

    let month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    let get_month = |m: &str| -> Option<usize> {
        month_names.iter().position(|&mon| mon == m).map(|i| i + 1)
    };

    let word_date_re = regex::Regex::new(r"([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})").unwrap();
    for cap in word_date_re.captures_iter(&matrix) {
        if let Some(m) = get_month(&cap[1]) {
            if let (Ok(d), Ok(y)) = (cap[2].parse::<u32>(), cap[3].parse::<u32>()) {
                mrefs.insert(format!("{:04}-{:02}-{:02}", y, m, d));
            }
        }
    }

    let mut releases = Vec::new();
    let blocks: Vec<&str> = changelogs.split("\n## ").collect();
    for (i, block) in blocks.iter().enumerate() {
        let text = if i == 0 { format!("{}", block) } else { format!("## {}", block) };
        if let Some(cap) = header_re.captures(&text) {
            if let Some(m) = get_month(&cap[1]) {
                if let (Ok(d), Ok(y)) = (cap[2].parse::<u32>(), cap[3].parse::<u32>()) {
                    let iso = format!("{:04}-{:02}-{:02}", y, m, d);
                    let header = text.lines().next().unwrap_or("").to_string();
                    let api = api_re.is_match(&text);
                    releases.push((iso, header, api));
                }
            }
        }
    }

    let total = releases.len();
    let mut api_total = 0;
    let mut gaps = Vec::new();

    for (iso, header, api) in releases {
        if api {
            api_total += 1;
            if !mrefs.contains(&iso) {
                gaps.push((iso, header));
            }
        }
    }

    if json_out {
        let unref: Vec<Value> = gaps.iter().map(|(iso, h)| serde_json::json!({"date": iso, "header": h})).collect();
        let report = serde_json::json!({
            "changelog_releases": total,
            "api_relevant_releases": api_total,
            "matrix_referenced_dates": mrefs.len(),
            "unreferenced_api_releases": unref,
        });
        println!("{}", serde_json::to_string_pretty(&report).unwrap());
    }

    if !json_out {
        println!("Changelog releases: {} ({} API-relevant). Matrix references {} dates.", total, api_total, mrefs.len());
        if gaps.is_empty() {
            println!("OK — every API-relevant changelog release is referenced in the version matrix.");
        } else {
            println!("WARN — {} API-relevant release(s) not referenced in pcx-version-matrix.md:", gaps.len());
            for (iso, h) in &gaps {
                println!("  {}  {}", iso, h);
            }
            println!("Review and add a matrix row for each, or confirm the release added no scripting API.");
        }
    }

    if !gaps.is_empty() && strict { 1 } else { 0 }
}
