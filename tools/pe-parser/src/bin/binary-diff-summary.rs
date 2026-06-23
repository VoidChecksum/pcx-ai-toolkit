use clap::Parser;
use pe_parser::{load_binary_data, parse_pe_bytes, section_data, Section};
use serde::Serialize;
use std::collections::{HashMap, HashSet};
use std::path::PathBuf;

const RECOMPILE_MIN_SAME: f64 = 70.0;
const RECOMPILE_MAX_DELTA: f64 = 1.0;
const REFACTOR_MIN_SAME: f64 = 30.0;
const MAJOR_MAX_DELTA: f64 = 10.0;

#[derive(Parser)]
#[command(about = "High-level diff summary between two binary versions")]
struct Args {
    #[arg(long)]
    old: PathBuf,
    #[arg(long)]
    new: PathBuf,
    #[arg(long)]
    sections: Option<String>,
    #[arg(long = "block-size", default_value_t = 4096)]
    block_size: usize,
    #[arg(long)]
    json: bool,
}

#[derive(Serialize, Clone)]
struct SectionDiff {
    name: String,
    old_size: usize,
    new_size: usize,
    size_delta: isize,
    old_blocks: usize,
    new_blocks: usize,
    identical: usize,
    changed: usize,
    new: usize,
    removed: usize,
    pct_identical: f64,
    pct_changed: f64,
    pct_new: f64,
    pct_removed: f64,
    #[serde(rename = "class", skip_serializing_if = "Option::is_none")]
    class_name: Option<String>,
}

#[derive(Serialize, Clone)]
struct Summary {
    pct_identical: f64,
    pct_changed: f64,
    classification: String,
    recommended_action: String,
}

#[derive(Serialize)]
struct Report {
    sections: Vec<SectionDiff>,
    summary: Summary,
    #[serde(skip_serializing_if = "Option::is_none")]
    old_binary: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    new_binary: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    block_size: Option<usize>,
}

fn action_for(classification: &str) -> &'static str {
    match classification {
        "RECOMPILE" => {
            "Offsets shifted, sigs likely survive. Patch-day re-sig viable; see skill://pcx-patch-day-playbook."
        }
        "REFACTOR" => {
            "Some sigs survive, many will not. Playbook applies but expect manual re-anchoring; see skill://pcx-patch-day-playbook."
        }
        _ => {
            "Block survival too low for a patch-day pass. Assume full re-RE; the playbook is insufficient on its own."
        }
    }
}

fn block_counts(blob: &[u8], block_size: usize) -> HashMap<Vec<u8>, usize> {
    let mut out = HashMap::new();
    for chunk in blob.chunks(block_size) {
        *out.entry(chunk.to_vec()).or_insert(0) += 1;
    }
    out
}

fn pct(n: usize, total: usize) -> f64 {
    if total == 0 {
        0.0
    } else {
        ((1000.0 * n as f64 / total as f64).round()) / 10.0
    }
}

fn round1(value: f64) -> f64 {
    (value * 10.0).round() / 10.0
}

fn diff_section(name: String, old_blob: &[u8], new_blob: &[u8], block_size: usize) -> SectionDiff {
    let old_counts = block_counts(old_blob, block_size);
    let new_counts = block_counts(new_blob, block_size);
    let old_blocks: usize = old_counts.values().sum();
    let new_blocks: usize = new_counts.values().sum();
    let mut identical = 0usize;

    for (block, old_count) in &old_counts {
        if let Some(new_count) = new_counts.get(block) {
            identical += (*old_count).min(*new_count);
        }
    }

    let new_only = new_blocks.saturating_sub(identical);
    let removed_only = old_blocks.saturating_sub(identical);
    let changed = new_only.min(removed_only);
    let net_new = new_only - changed;
    let net_removed = removed_only - changed;
    let total = old_blocks.max(new_blocks);

    SectionDiff {
        name,
        old_size: old_blob.len(),
        new_size: new_blob.len(),
        size_delta: new_blob.len() as isize - old_blob.len() as isize,
        old_blocks,
        new_blocks,
        identical,
        changed,
        new: net_new,
        removed: net_removed,
        pct_identical: pct(identical, total),
        pct_changed: pct(changed, total),
        pct_new: pct(net_new, total),
        pct_removed: pct(net_removed, total),
        class_name: None,
    }
}

fn size_delta_pct(diff: &SectionDiff) -> f64 {
    if diff.old_size == 0 {
        0.0
    } else {
        diff.size_delta.unsigned_abs() as f64 / diff.old_size as f64 * 100.0
    }
}

fn classify_text(diff: &SectionDiff) -> String {
    let same = diff.pct_identical;
    let delta = size_delta_pct(diff);
    if same < REFACTOR_MIN_SAME || delta > MAJOR_MAX_DELTA {
        return "MAJOR_CHANGE".to_string();
    }
    if same >= RECOMPILE_MIN_SAME && delta < RECOMPILE_MAX_DELTA {
        return "RECOMPILE".to_string();
    }
    "REFACTOR".to_string()
}

fn load_binary(path: &PathBuf) -> Result<(Vec<u8>, Vec<Section>), String> {
    let data = load_binary_data(path)?;
    let parsed = parse_pe_bytes(&data)?;
    Ok((data, parsed.sections))
}

fn build_report(
    old_data: &[u8],
    old_sections: &[Section],
    new_data: &[u8],
    new_sections: &[Section],
    want: Option<HashSet<String>>,
    block_size: usize,
) -> Report {
    let old_map: HashMap<String, Section> = old_sections
        .iter()
        .map(|sec| (sec.name.clone(), sec.clone()))
        .collect();
    let new_map: HashMap<String, Section> = new_sections
        .iter()
        .map(|sec| (sec.name.clone(), sec.clone()))
        .collect();

    let mut names: Vec<String> = new_sections.iter().map(|sec| sec.name.clone()).collect();
    for sec in old_sections {
        if !new_map.contains_key(&sec.name) {
            names.push(sec.name.clone());
        }
    }
    if let Some(want) = want {
        names.retain(|name| want.contains(name));
    }

    let mut sections = Vec::new();
    let mut classification: Option<String> = None;

    for name in names {
        let old_blob = old_map
            .get(&name)
            .map(|sec| section_data(old_data, sec))
            .unwrap_or(&[]);
        let new_blob = new_map
            .get(&name)
            .map(|sec| section_data(new_data, sec))
            .unwrap_or(&[]);
        let mut diff = diff_section(name.clone(), old_blob, new_blob, block_size);
        if name == ".text" {
            let class_name = classify_text(&diff);
            diff.class_name = Some(class_name.clone());
            classification = Some(class_name);
        }
        sections.push(diff);
    }

    let total: usize = sections
        .iter()
        .map(|sec| sec.old_blocks.max(sec.new_blocks))
        .sum();
    let same: usize = sections.iter().map(|sec| sec.identical).sum();
    let class_name = classification.unwrap_or_else(|| {
        let overall = pct(same, total);
        if overall >= RECOMPILE_MIN_SAME {
            "RECOMPILE".to_string()
        } else if overall >= REFACTOR_MIN_SAME {
            "REFACTOR".to_string()
        } else {
            "MAJOR_CHANGE".to_string()
        }
    });
    let pct_identical = pct(same, total);
    let summary = Summary {
        pct_identical,
        pct_changed: round1(100.0 - pct_identical),
        recommended_action: action_for(&class_name).to_string(),
        classification: class_name,
    };

    Report {
        sections,
        summary,
        old_binary: None,
        new_binary: None,
        block_size: None,
    }
}

fn fmt_delta(delta: isize) -> String {
    if delta >= 0 {
        format!("+{delta}")
    } else {
        format!("-{}", delta.unsigned_abs())
    }
}

fn print_report(report: &Report, old_name: &str, new_name: &str) {
    println!("OLD: {old_name}");
    println!("NEW: {new_name}");
    println!();
    let hdr = format!(
        "{:<10}{:>11}{:>11}{:>11}{:>8}{:>8}{:>8}{:>8}  CLASS",
        "SECTION", "OLD", "NEW", "DELTA", "%SAME", "%CHG", "%NEW", "%DEL"
    );
    println!("{hdr}");
    println!("{}", "-".repeat(hdr.len()));
    for sec in &report.sections {
        println!(
            "{:<10}{:>11}{:>11}{:>11}{:>8.1}{:>8.1}{:>8.1}{:>8.1}  {}",
            sec.name,
            sec.old_size,
            sec.new_size,
            fmt_delta(sec.size_delta),
            sec.pct_identical,
            sec.pct_changed,
            sec.pct_new,
            sec.pct_removed,
            sec.class_name.as_deref().unwrap_or("-")
        );
    }
    println!();
    println!(
        "Overall: {:.1}% identical, {:.1}% changed",
        report.summary.pct_identical, report.summary.pct_changed
    );
    println!("Verdict: {}", report.summary.classification);
    println!("Action:  {}", report.summary.recommended_action);
}

fn basename(path: &PathBuf) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_else(|| path.to_str().unwrap_or(""))
        .to_string()
}

fn main() {
    let args = Args::parse();
    if args.block_size == 0 {
        eprintln!("Error: --block-size must be >= 1");
        std::process::exit(1);
    }

    let (old_data, old_sections) = match load_binary(&args.old) {
        Ok(value) => value,
        Err(e) => {
            eprintln!("Error: {}: {e}", args.old.display());
            std::process::exit(1);
        }
    };
    let (new_data, new_sections) = match load_binary(&args.new) {
        Ok(value) => value,
        Err(e) => {
            eprintln!("Error: {}: {e}", args.new.display());
            std::process::exit(1);
        }
    };
    let want = args.sections.as_ref().map(|sections| {
        sections
            .split(',')
            .map(|name| name.trim().to_string())
            .filter(|name| !name.is_empty())
            .collect::<HashSet<_>>()
    });
    let mut report = build_report(
        &old_data,
        &old_sections,
        &new_data,
        &new_sections,
        want,
        args.block_size,
    );
    if report.sections.is_empty() {
        eprintln!("Error: no matching sections to compare");
        std::process::exit(1);
    }

    let old_name = basename(&args.old);
    let new_name = basename(&args.new);
    if args.json {
        report.old_binary = Some(old_name);
        report.new_binary = Some(new_name);
        report.block_size = Some(args.block_size);
        println!("{}", serde_json::to_string_pretty(&report).unwrap());
        return;
    }
    print_report(&report, &old_name, &new_name);
}
