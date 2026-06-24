use clap::Parser;
use pe_parser::{load_binary_data, parse_pe_bytes, Export};
use serde::Serialize;
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Parser)]
#[command(about = "Map binary exports and optional neighbouring consumers")]
struct Args {
    binary: PathBuf,
    #[arg(long)]
    consumers: Option<PathBuf>,
    #[arg(long)]
    filter: Option<String>,
    #[arg(long = "ordinal-only")]
    ordinal_only: bool,
    #[arg(long)]
    json: bool,
}

#[derive(Serialize, Clone)]
struct ExportRow {
    ordinal: u32,
    name: Option<String>,
    rva: String,
    forward: Option<String>,
    hint: Option<String>,
    consumers: Vec<String>,
}

#[derive(Serialize)]
struct Output {
    module: String,
    exports: Vec<ExportRow>,
    #[serde(skip_serializing_if = "Option::is_none")]
    note: Option<String>,
}

fn basename(path: &Path) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_else(|| path.to_str().unwrap_or(""))
        .to_string()
}

fn mangle_hint(name: &str) -> Option<String> {
    if let Some(rest) = name.strip_prefix('?') {
        let end = rest.find('@').unwrap_or(rest.len());
        return Some(rest[..end].to_string()).filter(|s| !s.is_empty());
    }
    if let Some(rest) = name.strip_prefix("_Z") {
        let mut s = rest;
        if let Some(trimmed) = s.strip_prefix('N') {
            s = trimmed;
        }
        let bytes = s.as_bytes();
        let mut parts = Vec::new();
        let mut i = 0usize;
        while i < bytes.len() && bytes[i].is_ascii_digit() {
            let mut j = i;
            while j < bytes.len() && bytes[j].is_ascii_digit() {
                j += 1;
            }
            let Ok(n) = s[i..j].parse::<usize>() else {
                break;
            };
            if j + n > s.len() {
                break;
            }
            parts.push(s[j..j + n].to_string());
            i = j + n;
        }
        if !parts.is_empty() {
            return Some(parts.join("::"));
        }
    }
    None
}

fn export_rows(exports: &[Export]) -> Vec<ExportRow> {
    exports
        .iter()
        .map(|export| ExportRow {
            ordinal: export.ordinal,
            name: (!export.name.starts_with("Ordinal")).then(|| export.name.clone()),
            rva: format!("0x{:X}", export.rva),
            forward: export.forwarder.clone(),
            hint: (!export.name.starts_with("Ordinal"))
                .then(|| mangle_hint(&export.name))
                .flatten(),
            consumers: Vec::new(),
        })
        .collect()
}

fn imported_named_symbols(
    path: &Path,
    target_names: &HashSet<String>,
) -> Option<(String, HashSet<String>)> {
    let data = load_binary_data(path).ok()?;
    let parsed = parse_pe_bytes(&data).ok()?;
    let mut names = HashSet::new();
    for import in parsed.imports {
        let Some((dll, func)) = import.split_once('!') else {
            continue;
        };
        if target_names.contains(&dll.to_lowercase()) {
            names.insert(func.to_string());
        }
    }
    Some((basename(path), names))
}

fn attach_consumers(target: &Path, module: &str, consumer_dir: &Path, exports: &mut [ExportRow]) {
    let mut target_names = HashSet::from([basename(target).to_lowercase(), module.to_lowercase()]);
    if let Some(stem) = target.file_stem().and_then(|s| s.to_str()) {
        target_names.insert(format!("{stem}.dll").to_lowercase());
        target_names.insert(format!("{stem}.exe").to_lowercase());
    }
    let by_name: HashMap<String, usize> = exports
        .iter()
        .enumerate()
        .filter_map(|(idx, row)| row.name.as_ref().map(|name| (name.clone(), idx)))
        .collect();
    let Ok(entries) = fs::read_dir(consumer_dir) else {
        return;
    };
    let target_abs = target.canonicalize().ok();
    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_file() {
            continue;
        }
        let ext = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| ext.to_ascii_lowercase());
        if !matches!(ext.as_deref(), Some("dll" | "exe")) {
            continue;
        }
        if target_abs
            .as_ref()
            .is_some_and(|abs| path.canonicalize().ok().as_ref() == Some(abs))
        {
            continue;
        }
        let Some((consumer, names)) = imported_named_symbols(&path, &target_names) else {
            continue;
        };
        for name in names {
            if let Some(idx) = by_name.get(&name).copied() {
                exports[idx].consumers.push(consumer.clone());
            }
        }
    }
    for row in exports {
        row.consumers.sort();
        row.consumers.dedup();
    }
}

fn select(
    mut exports: Vec<ExportRow>,
    filter: Option<&String>,
    ordinal_only: bool,
) -> Vec<ExportRow> {
    if ordinal_only {
        exports.retain(|row| row.name.is_none());
    }
    if let Some(filter) = filter {
        let filter = filter.to_lowercase();
        exports.retain(|row| {
            row.name
                .as_ref()
                .is_some_and(|name| name.to_lowercase().contains(&filter))
                || row
                    .hint
                    .as_ref()
                    .is_some_and(|hint| hint.to_lowercase().contains(&filter))
        });
    }
    exports
}

fn print_table(module: &str, exports: &[ExportRow], with_consumers: bool) {
    println!("MODULE: {module}  ({} exports shown)", exports.len());
    println!(
        "{:>6}  {:<40}  {:<10}  {}",
        "ORD",
        "NAME",
        "RVA",
        if with_consumers { "CONSUMERS" } else { "HINT" }
    );
    for export in exports {
        let mut name = export
            .name
            .clone()
            .unwrap_or_else(|| "<ordinal-only>".to_string());
        if let Some(forward) = &export.forward {
            name = format!("{name}  FORWARD -> {forward}");
        }
        let tail = if with_consumers {
            if export.consumers.is_empty() {
                "0".to_string()
            } else {
                format!(
                    "{}  {}",
                    export.consumers.len(),
                    export.consumers.join(", ")
                )
            }
        } else {
            export.hint.clone().unwrap_or_default()
        };
        println!(
            "{:>6}  {:<40}  {:<10}  {}",
            export.ordinal, name, export.rva, tail
        );
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
    let parsed = match parse_pe_bytes(&data) {
        Ok(parsed) => parsed,
        Err(e) => {
            eprintln!("Error: {} is not a valid PE: {e}", args.binary.display());
            std::process::exit(1);
        }
    };
    let module = basename(&args.binary);
    let mut exports = export_rows(&parsed.exports);
    if exports.is_empty() {
        let out = Output {
            module: args.binary.display().to_string(),
            exports,
            note: Some("no export directory".to_string()),
        };
        if args.json {
            println!("{}", serde_json::to_string_pretty(&out).unwrap());
        } else {
            println!(
                "{}: no export directory (binary has no exports).",
                args.binary.display()
            );
        }
        return;
    }
    if let Some(dir) = &args.consumers {
        if !dir.is_dir() {
            eprintln!("Error: {} is not a directory", dir.display());
            std::process::exit(1);
        }
        attach_consumers(&args.binary, &module, dir, &mut exports);
    }
    let shown = select(exports, args.filter.as_ref(), args.ordinal_only);
    if args.json {
        println!(
            "{}",
            serde_json::to_string_pretty(&Output {
                module,
                exports: shown,
                note: None,
            })
            .unwrap()
        );
        return;
    }
    print_table(&module, &shown, args.consumers.is_some());
}
