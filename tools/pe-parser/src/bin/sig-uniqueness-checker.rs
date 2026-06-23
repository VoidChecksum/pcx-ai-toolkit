use clap::Parser;
use pe_parser::{
    format_byte_pattern, load_binary_data, parse_byte_pattern, parse_pe_bytes, scan_pattern,
    section_data,
};
use serde::Serialize;
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Check whether a byte signature uniquely identifies one instruction")]
struct Args {
    binary: PathBuf,
    #[arg(long)]
    sig: Option<String>,
    #[arg(long = "sig-file")]
    sig_file: Option<PathBuf>,
    #[arg(long)]
    sections: Option<String>,
    #[arg(long = "near-misses", default_value_t = 0)]
    near_misses: usize,
    #[arg(long)]
    json: bool,
}

#[derive(Serialize, Clone)]
struct Hit {
    section: String,
    file_offset: u32,
    rva: u32,
    context: String,
}

#[derive(Serialize)]
struct Probe {
    wildcarded: usize,
    matches: usize,
}

#[derive(Serialize)]
struct NearMiss {
    section: String,
    file_offset: u32,
    rva: u32,
    distance: usize,
    diff_indices: Vec<usize>,
}

#[derive(Serialize)]
struct ResultRow {
    name: String,
    pattern: String,
    length: usize,
    matches: usize,
    hits: Vec<Hit>,
    verdict: String,
    hint: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    margin: Option<usize>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    probe: Vec<Probe>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    near_misses: Vec<NearMiss>,
}

fn load_sigs(args: &Args) -> Result<Vec<(String, Vec<Option<u8>>)>, String> {
    if let Some(sig) = &args.sig {
        return Ok(vec![("sig".to_string(), parse_byte_pattern(sig)?)]);
    }
    let path = args
        .sig_file
        .as_ref()
        .ok_or_else(|| "one of --sig or --sig-file is required".to_string())?;
    let text = fs::read_to_string(path).map_err(|e| format!("{e}"))?;
    let mut out = Vec::new();
    for raw in text.lines() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let (name, sig) = line
            .split_once('=')
            .ok_or_else(|| format!("expected name=sig: {line}"))?;
        out.push((name.trim().to_string(), parse_byte_pattern(sig.trim())?));
    }
    if out.is_empty() {
        return Err("sig file has no entries".to_string());
    }
    Ok(out)
}

fn context_hex(buf: &[u8], start: usize) -> String {
    buf[start..buf.len().min(start + 16)]
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect::<Vec<_>>()
        .join(" ")
}

fn hits_for(data: &[u8], sections: &[pe_parser::Section], pattern: &[Option<u8>]) -> Vec<Hit> {
    let mut hits = Vec::new();
    for sec in sections {
        let buf = section_data(data, sec);
        for idx in scan_pattern(buf, pattern) {
            hits.push(Hit {
                section: sec.name.clone(),
                file_offset: sec.raddr + idx as u32,
                rva: sec.vaddr + idx as u32,
                context: context_hex(buf, idx),
            });
        }
    }
    hits
}

fn count_for(data: &[u8], sections: &[pe_parser::Section], pattern: &[Option<u8>]) -> usize {
    sections
        .iter()
        .map(|sec| scan_pattern(section_data(data, sec), pattern).len())
        .sum()
}

fn uniqueness_margin(
    data: &[u8],
    sections: &[pe_parser::Section],
    pattern: &[Option<u8>],
) -> usize {
    let mut shortest = pattern.len();
    for len in (1..pattern.len()).rev() {
        if count_for(data, sections, &pattern[..len]) == 1 {
            shortest = len;
        } else {
            break;
        }
    }
    pattern.len() - shortest
}

fn trailing_probe(
    data: &[u8],
    sections: &[pe_parser::Section],
    pattern: &[Option<u8>],
) -> Vec<Probe> {
    [1usize, 2, 4]
        .iter()
        .filter_map(|k| {
            if *k >= pattern.len() {
                return None;
            }
            let mut probe = pattern.to_vec();
            for idx in probe.len() - *k..probe.len() {
                probe[idx] = None;
            }
            Some(Probe {
                wildcarded: *k,
                matches: count_for(data, sections, &probe),
            })
        })
        .collect()
}

fn near_misses(
    data: &[u8],
    sections: &[pe_parser::Section],
    pattern: &[Option<u8>],
    max_dist: usize,
) -> Vec<NearMiss> {
    if max_dist == 0 {
        return Vec::new();
    }
    let fixed: Vec<(usize, u8)> = pattern
        .iter()
        .enumerate()
        .filter_map(|(idx, b)| b.map(|v| (idx, v)))
        .collect();
    let mut out = Vec::new();
    for sec in sections {
        let buf = section_data(data, sec);
        if pattern.len() > buf.len() {
            continue;
        }
        for start in 0..=buf.len() - pattern.len() {
            let mut diff = Vec::new();
            for (idx, byte) in &fixed {
                if buf[start + idx] != *byte {
                    diff.push(*idx);
                    if diff.len() > max_dist {
                        break;
                    }
                }
            }
            if !diff.is_empty() && diff.len() <= max_dist {
                out.push(NearMiss {
                    section: sec.name.clone(),
                    file_offset: sec.raddr + start as u32,
                    rva: sec.vaddr + start as u32,
                    distance: diff.len(),
                    diff_indices: diff,
                });
                if out.len() >= 20 {
                    return out;
                }
            }
        }
    }
    out
}

fn analyze(
    data: &[u8],
    sections: &[pe_parser::Section],
    name: String,
    pattern: Vec<Option<u8>>,
    near: usize,
) -> ResultRow {
    let hits = hits_for(data, sections, &pattern);
    let matches = hits.len();
    let mut margin = None;
    let mut probe = Vec::new();
    let (verdict, hint) = if matches == 1 {
        let m = uniqueness_margin(data, sections, &pattern);
        margin = Some(m);
        if m == 0 {
            (
                "BRITTLE".to_string(),
                "Every byte is load-bearing; one patched byte makes it stale. Append stable trailing context for a safety margin.".to_string(),
            )
        } else if m >= 8 {
            let keep = pattern.len() - m;
            (
                "UNIQUE".to_string(),
                format!(
                    "Overspecified by {m} bytes; could shorten to \"{}\" and stay unique.",
                    format_byte_pattern(&pattern[..keep])
                ),
            )
        } else {
            (
                "UNIQUE".to_string(),
                format!("Unique with a {m}-byte margin."),
            )
        }
    } else if matches == 0 {
        probe = trailing_probe(data, sections, &pattern);
        let hit = probe.iter().find(|p| p.matches >= 1);
        let hint = match hit {
            Some(p) => format!(
                "Wildcarding the last {} byte(s) yields {} match(es) - a trailing byte changed; re-dump there.",
                p.wildcarded, p.matches
            ),
            None => "No trailing variant matches; the region moved or was removed. Re-generate.".to_string(),
        };
        ("STALE".to_string(), hint)
    } else {
        (
            "AMBIGUOUS".to_string(),
            format!("{matches} matches; lengthen the sig with following bytes to disambiguate."),
        )
    };

    ResultRow {
        name,
        pattern: format_byte_pattern(&pattern),
        length: pattern.len(),
        matches,
        hits,
        verdict,
        hint,
        margin,
        probe,
        near_misses: near_misses(data, sections, &pattern, near),
    }
}

fn print_result(row: &ResultRow) {
    println!("SIG {} = {}  ({} bytes)", row.name, row.pattern, row.length);
    println!("  Verdict: {}   Matches: {}", row.verdict, row.matches);
    for hit in &row.hits {
        println!(
            "    {:<8} off=0x{:X}  rva=0x{:X}  ctx: {}",
            hit.section, hit.file_offset, hit.rva, hit.context
        );
    }
    if let Some(margin) = row.margin {
        println!("  Margin: {margin} trailing byte(s) removable while still unique");
    }
    for probe in &row.probe {
        println!(
            "    last {} wildcarded -> {} match(es)",
            probe.wildcarded, probe.matches
        );
    }
    for nm in &row.near_misses {
        let cols = nm
            .diff_indices
            .iter()
            .map(|i| i.to_string())
            .collect::<Vec<_>>()
            .join(",");
        println!(
            "    near rva=0x{:X}  dist={}  differs at byte idx [{}] -> wildcard these to widen",
            nm.rva, nm.distance, cols
        );
    }
    println!("  Hint: {}\n", row.hint);
}

fn main() {
    let args = Args::parse();
    if args.sig.is_none() == args.sig_file.is_none() {
        eprintln!("Error: exactly one of --sig or --sig-file is required");
        std::process::exit(2);
    }
    let data = match load_binary_data(&args.binary) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    };
    let parsed = match parse_pe_bytes(&data) {
        Ok(parsed) => parsed,
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    };
    let want: Option<Vec<String>> = args
        .sections
        .as_ref()
        .map(|s| s.split(',').map(|x| x.trim().to_string()).collect());
    let sections: Vec<_> = parsed
        .sections
        .iter()
        .filter(|sec| match &want {
            Some(names) => names.iter().any(|n| n == &sec.name),
            None => sec.exec,
        })
        .cloned()
        .collect();
    if sections.is_empty() {
        eprintln!("Error: no matching sections to scan");
        std::process::exit(1);
    }
    let sigs = match load_sigs(&args) {
        Ok(sigs) => sigs,
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    };
    let rows: Vec<_> = sigs
        .into_iter()
        .map(|(name, pattern)| analyze(&data, &sections, name, pattern, args.near_misses))
        .collect();
    if args.json {
        println!("{}", serde_json::to_string_pretty(&rows).unwrap());
        return;
    }
    println!(
        "File: {}  Sections scanned: {}\n",
        args.binary.display(),
        sections
            .iter()
            .map(|s| s.name.as_str())
            .collect::<Vec<_>>()
            .join(", ")
    );
    for row in &rows {
        print_result(row);
    }
}
