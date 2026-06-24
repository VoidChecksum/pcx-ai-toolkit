use clap::Parser;
use pe_parser::{load_binary_data, parse_pe_bytes, section_data};
use serde::Serialize;
use std::collections::HashSet;
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Extract likely single-byte XOR-encrypted strings")]
struct Args {
    binary: PathBuf,
    #[arg(long)]
    key: Option<String>,
    #[arg(long = "min-length", default_value_t = 6)]
    min_length: usize,
    #[arg(long)]
    section: Option<String>,
    #[arg(long)]
    json: bool,
}

#[derive(Clone)]
struct Region {
    name: String,
    offset: usize,
    size: usize,
}

#[derive(Serialize, Clone)]
struct Hit {
    offset: usize,
    key: String,
    length: usize,
    string: String,
    section: String,
}

fn parse_key(key: Option<&String>) -> Result<Option<u8>, String> {
    match key {
        None => Ok(None),
        Some(value) => {
            let trimmed = value.trim();
            let trimmed = trimmed.strip_prefix("0x").unwrap_or(trimmed);
            let byte = u8::from_str_radix(trimmed, 16)
                .map_err(|_| format!("invalid --key value {value:?}"))?;
            if byte == 0 {
                return Err("--key must not be 0x00".to_string());
            }
            Ok(Some(byte))
        }
    }
}

fn printable(byte: u8) -> bool {
    matches!(byte, 0x09 | 0x0A | 0x0D | 0x20..=0x7E)
}

fn find_xor_strings(data: &[u8], min_length: usize, key: Option<u8>) -> Vec<Hit> {
    let keys: Vec<u8> = match key {
        Some(k) => vec![k],
        None => (1u8..=255).collect(),
    };
    let mut results = Vec::new();
    for k in keys {
        let mut i = 0usize;
        while i < data.len() {
            let decoded = data[i] ^ k;
            if printable(decoded) && decoded != 0 {
                let start = i;
                let mut plain = Vec::new();
                while i < data.len() {
                    let b = data[i] ^ k;
                    if !printable(b) || b == 0 {
                        break;
                    }
                    plain.push(b);
                    i += 1;
                }
                if plain.len() >= min_length {
                    let text = String::from_utf8_lossy(&plain).trim().to_string();
                    let alnum = text.chars().filter(|c| c.is_ascii_alphanumeric()).count();
                    if alnum as f64 / text.len().max(1) as f64 >= 0.5 {
                        let original = &data[start..start + plain.len()];
                        let orig_printable = original.iter().filter(|b| printable(**b)).count();
                        if orig_printable as f64 / (original.len().max(1) as f64) < 0.8 {
                            results.push(Hit {
                                offset: start,
                                key: format!("0x{k:02X}"),
                                length: plain.len(),
                                string: text,
                                section: String::new(),
                            });
                        }
                    }
                }
                i += 1;
            } else {
                i += 1;
            }
        }
    }
    results.sort_by_key(|hit| (std::cmp::Reverse(hit.length), hit.offset));
    let mut seen = HashSet::new();
    let mut unique = Vec::new();
    for hit in results {
        if seen.insert(hit.offset) {
            unique.push(hit);
        }
    }
    unique.sort_by_key(|hit| hit.offset);
    unique
}

fn basename(path: &PathBuf) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_else(|| path.to_str().unwrap_or(""))
        .to_string()
}

fn regions(data: &[u8], path: &PathBuf, section: Option<&String>) -> Result<Vec<Region>, String> {
    match parse_pe_bytes(data) {
        Ok(pe) => {
            let mut out = Vec::new();
            for sec in &pe.sections {
                if sec.rsize == 0 {
                    continue;
                }
                if section.is_some_and(|want| want != &sec.name) {
                    continue;
                }
                let blob = section_data(data, sec);
                out.push(Region {
                    name: sec.name.clone(),
                    offset: sec.raddr as usize,
                    size: blob.len(),
                });
            }
            if section.is_some() && out.is_empty() {
                let names = pe
                    .sections
                    .iter()
                    .map(|sec| sec.name.as_str())
                    .collect::<Vec<_>>()
                    .join(", ");
                return Err(format!(
                    "Section {:?} not found. Available: {names}",
                    section.unwrap()
                ));
            }
            Ok(out)
        }
        Err(_) => {
            if section.is_some() {
                Err(format!("{} is not a recognized binary", path.display()))
            } else {
                Ok(vec![Region {
                    name: "raw".to_string(),
                    offset: 0,
                    size: data.len(),
                }])
            }
        }
    }
}

fn main() {
    let args = Args::parse();
    let data = match load_binary_data(&args.binary) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    };
    let key = match parse_key(args.key.as_ref()) {
        Ok(key) => key,
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    };
    let regions = match regions(&data, &args.binary, args.section.as_ref()) {
        Ok(regions) => regions,
        Err(e) => {
            eprintln!("{e}");
            std::process::exit(1);
        }
    };

    let mut hits = Vec::new();
    for region in &regions {
        let end = region.offset.saturating_add(region.size).min(data.len());
        let mut region_hits = find_xor_strings(&data[region.offset..end], args.min_length, key);
        for hit in &mut region_hits {
            hit.offset += region.offset;
            hit.section.clone_from(&region.name);
        }
        hits.extend(region_hits);
    }

    if args.json {
        println!("{}", serde_json::to_string_pretty(&hits).unwrap());
        return;
    }

    println!("File: {} ({} bytes)", basename(&args.binary), data.len());
    let key_desc = args
        .key
        .as_deref()
        .map(|k| format!("key {k}"))
        .unwrap_or_else(|| "all keys (0x01-0xFF)".to_string());
    println!("Scanning {} section(s) with {}", regions.len(), key_desc);
    println!();
    if hits.is_empty() {
        println!("No XOR-encrypted strings found.");
        return;
    }
    println!("Found {} encrypted string(s):\n", hits.len());
    for hit in hits.iter().take(200) {
        println!(
            "  0x{:08X}  key={}  [{:>8}]  \"{}\"",
            hit.offset, hit.key, hit.section, hit.string
        );
    }
    if hits.len() > 200 {
        println!("  ... and {} more", hits.len() - 200);
    }
}
