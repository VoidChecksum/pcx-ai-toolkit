use clap::Parser;
use pe_parser::{load_binary_data, parse_byte_pattern, parse_pe_bytes, scan_pattern, section_data};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Diff named offsets between two binary versions")]
struct Args {
    #[arg(long)]
    old: PathBuf,
    #[arg(long)]
    new: PathBuf,
    #[arg(long)]
    sigs: PathBuf,
    #[arg(long)]
    json: bool,
}

#[derive(Deserialize)]
struct Sig {
    name: String,
    pattern: String,
    #[serde(default = "default_kind")]
    kind: String,
    rip_offset: Option<usize>,
    insn_len: Option<i64>,
}

#[derive(Serialize, Clone)]
struct Hit {
    file_off: u32,
    rva: u32,
    resolved: i64,
}

#[derive(Serialize)]
struct OffsetRow {
    name: String,
    kind: String,
    old: Option<Hit>,
    new: Option<Hit>,
    delta: Option<String>,
    status: String,
}

#[derive(Serialize)]
struct Summary {
    moved: usize,
    unchanged: usize,
    lost: usize,
}

#[derive(Serialize)]
struct ResultDoc {
    old_binary: String,
    new_binary: String,
    offsets: Vec<OffsetRow>,
    summary: Summary,
}

fn default_kind() -> String {
    "direct".to_string()
}

fn scan_sig(data: &[u8], sections: &[pe_parser::Section], sig: &Sig) -> Result<Vec<Hit>, String> {
    let pattern = parse_byte_pattern(&sig.pattern)?;
    let mut hits = Vec::new();
    for sec in sections.iter().filter(|sec| sec.exec) {
        let blob = section_data(data, sec);
        for idx in scan_pattern(blob, &pattern) {
            let file_off = sec.raddr + idx as u32;
            let rva = sec.vaddr + idx as u32;
            let mut resolved = rva as i64;
            if sig.kind == "rip" {
                let rip_offset = sig
                    .rip_offset
                    .ok_or_else(|| format!("{}: kind=rip requires rip_offset", sig.name))?;
                let insn_len = sig
                    .insn_len
                    .ok_or_else(|| format!("{}: kind=rip requires insn_len", sig.name))?;
                let disp_off = file_off as usize + rip_offset;
                if disp_off + 4 > data.len() {
                    continue;
                }
                let disp = i32::from_le_bytes(data[disp_off..disp_off + 4].try_into().unwrap());
                resolved = rva as i64 + insn_len + disp as i64;
            }
            hits.push(Hit {
                file_off,
                rva,
                resolved,
            });
        }
    }
    Ok(hits)
}

fn shex(delta: i64) -> String {
    if delta < 0 {
        format!("-0x{:X}", delta.unsigned_abs())
    } else {
        format!("+0x{delta:X}")
    }
}

fn hex_i64(value: i64) -> String {
    if value < 0 {
        format!("-0x{:X}", value.unsigned_abs())
    } else {
        format!("0x{value:X}")
    }
}

fn addr_str(hit: Option<&Hit>) -> String {
    match hit {
        None => "-".to_string(),
        Some(hit) if hit.resolved != hit.rva as i64 => {
            format!("0x{:X}->{}", hit.rva, hex_i64(hit.resolved))
        }
        Some(hit) => format!("0x{:X}", hit.rva),
    }
}

fn classify(old_hits: &[Hit], new_hits: &[Hit]) -> (&'static str, Option<i64>) {
    if old_hits.len() > 1 {
        return ("MULTIPLE_HITS_OLD", None);
    }
    if new_hits.len() > 1 {
        return ("MULTIPLE_HITS_NEW", None);
    }
    if !old_hits.is_empty() && new_hits.is_empty() {
        return ("LOST_IN_NEW", None);
    }
    if !new_hits.is_empty() && old_hits.is_empty() {
        return ("NEW_IN_NEW", None);
    }
    if old_hits.is_empty() && new_hits.is_empty() {
        return ("LOST_IN_NEW", None);
    }
    let delta = new_hits[0].resolved - old_hits[0].resolved;
    if delta == 0 {
        ("UNCHANGED", Some(delta))
    } else {
        ("MOVED", Some(delta))
    }
}

fn diff(
    old_data: &[u8],
    new_data: &[u8],
    old_sections: &[pe_parser::Section],
    new_sections: &[pe_parser::Section],
    sigs: &[Sig],
) -> Result<(Vec<OffsetRow>, Summary), String> {
    let mut offsets = Vec::new();
    let mut summary = Summary {
        moved: 0,
        unchanged: 0,
        lost: 0,
    };

    for sig in sigs {
        if sig.kind != "direct" && sig.kind != "rip" {
            return Err(format!("{}: unsupported kind {:?}", sig.name, sig.kind));
        }
        let old_hits = scan_sig(old_data, old_sections, sig)?;
        let new_hits = scan_sig(new_data, new_sections, sig)?;
        let (status, delta) = classify(&old_hits, &new_hits);
        match status {
            "MOVED" => summary.moved += 1,
            "UNCHANGED" => summary.unchanged += 1,
            "LOST_IN_NEW" => summary.lost += 1,
            _ => {}
        }
        offsets.push(OffsetRow {
            name: sig.name.clone(),
            kind: sig.kind.clone(),
            old: (old_hits.len() == 1).then(|| old_hits[0].clone()),
            new: (new_hits.len() == 1).then(|| new_hits[0].clone()),
            delta: delta.map(shex),
            status: status.to_string(),
        });
    }

    Ok((offsets, summary))
}

fn load_binary(path: &PathBuf) -> Result<(Vec<u8>, Vec<pe_parser::Section>), String> {
    let data = load_binary_data(path)?;
    let parsed = parse_pe_bytes(&data)?;
    Ok((data, parsed.sections))
}

fn load_sigs(path: &PathBuf) -> Result<Vec<Sig>, String> {
    let text = fs::read_to_string(path).map_err(|e| format!("{e}"))?;
    let sigs: Vec<Sig> = serde_json::from_str(&text).map_err(|e| format!("{e}"))?;
    if sigs.is_empty() {
        return Err("--sigs must be a non-empty JSON list".to_string());
    }
    Ok(sigs)
}

fn basename(path: &PathBuf) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_else(|| path.to_str().unwrap_or(""))
        .to_string()
}

fn print_table(result: &ResultDoc) {
    println!("OLD: {}", result.old_binary);
    println!("NEW: {}", result.new_binary);
    println!();
    let hdr = format!(
        "{:<22}{:<8}{:<26}{:<26}{:<14}STATUS",
        "NAME", "KIND", "OLD", "NEW", "DELTA"
    );
    println!("{hdr}");
    println!("{}", "-".repeat(hdr.len()));
    for row in &result.offsets {
        println!(
            "{:<22}{:<8}{:<26}{:<26}{:<14}{}",
            row.name,
            row.kind,
            addr_str(row.old.as_ref()),
            addr_str(row.new.as_ref()),
            row.delta.as_deref().unwrap_or("-"),
            row.status
        );
    }
    println!();
    println!(
        "Summary: {} moved, {} unchanged, {} lost",
        result.summary.moved, result.summary.unchanged, result.summary.lost
    );
}

fn main() {
    let args = Args::parse();
    let sigs = match load_sigs(&args.sigs) {
        Ok(sigs) => sigs,
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    };
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
    let (offsets, summary) = match diff(&old_data, &new_data, &old_sections, &new_sections, &sigs) {
        Ok(value) => value,
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    };
    let result = ResultDoc {
        old_binary: basename(&args.old),
        new_binary: basename(&args.new),
        offsets,
        summary,
    };

    if args.json {
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
        return;
    }
    print_table(&result);
}
