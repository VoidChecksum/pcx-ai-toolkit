use clap::Parser;
use pe_parser::{load_binary_data, parse_pe_bytes, section_data};
use serde::Serialize;
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Identify binary protectors by sections, imports, and byte signatures")]
struct Args {
    binary: PathBuf,
    #[arg(long)]
    json: bool,
}

#[derive(Serialize, Clone)]
struct Protector {
    name: String,
    evidence: String,
}

#[derive(Serialize)]
struct Report {
    file: String,
    size: usize,
    arch: String,
    entry_rva: String,
    sections: usize,
    imports: usize,
    protectors: Vec<Protector>,
    indicators: Vec<String>,
    anti_debug: Vec<String>,
}

fn section_sigs() -> &'static [(&'static str, &'static str)] {
    &[
        (".vmp0", "VMProtect"),
        (".vmp1", "VMProtect"),
        (".vmp2", "VMProtect"),
        (".themida", "Themida / WinLicense"),
        (".winlice", "Themida / WinLicense"),
        ("Themida", "Themida (legacy)"),
        (".cv", "Code Virtualizer"),
        (".enigma", "Enigma Protector"),
        (".enigm", "Enigma Protector"),
        (".obsidiu", "Obsidium"),
        (".aspack", "ASPack"),
        (".adata", "ASPack"),
        ("UPX0", "UPX"),
        ("UPX1", "UPX"),
        ("UPX2", "UPX"),
        (".nsp0", "NSPack"),
        (".nsp1", "NSPack"),
        (".petite", "Petite"),
        (".MPRESS", "MPRESS"),
        (".perplex", "Perplex"),
        ("PEC2", "PECompact"),
        (".sforce", "StarForce"),
        (".denuvo", "Denuvo"),
    ]
}

fn anti_debug_imports() -> &'static [&'static str] {
    &[
        "IsDebuggerPresent",
        "CheckRemoteDebuggerPresent",
        "NtQueryInformationProcess",
        "NtSetInformationThread",
        "OutputDebugStringA",
        "GetTickCount",
        "QueryPerformanceCounter",
    ]
}

fn basename(path: &PathBuf) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_else(|| path.to_str().unwrap_or(""))
        .to_string()
}

fn contains_bytes(haystack: &[u8], needle: &[u8]) -> bool {
    needle.len() <= haystack.len() && haystack.windows(needle.len()).any(|w| w == needle)
}

fn count_bytes(haystack: &[u8], needle: &[u8]) -> usize {
    if needle.is_empty() || needle.len() > haystack.len() {
        return 0;
    }
    haystack
        .windows(needle.len())
        .filter(|w| *w == needle)
        .count()
}

fn analyze(path: &PathBuf) -> Result<Report, String> {
    let data = load_binary_data(path)?;
    let pe = parse_pe_bytes(&data)?;
    let mut protectors = Vec::new();
    let mut indicators = Vec::new();
    let mut anti_debug = Vec::new();

    for sec in &pe.sections {
        for (sig, name) in section_sigs() {
            if sec
                .name
                .as_bytes()
                .windows(sig.len())
                .any(|w| w == sig.as_bytes())
            {
                if !protectors.iter().any(|p: &Protector| p.name == *name) {
                    protectors.push(Protector {
                        name: (*name).to_string(),
                        evidence: format!("section '{}'", sec.name),
                    });
                }
            }
        }
        if sec.rsize > 0 && sec.vsize > sec.rsize * 3 {
            indicators.push(format!(
                "section '{}' is packed (VS=0x{:X} >> RS=0x{:X})",
                sec.name, sec.vsize, sec.rsize
            ));
        }
        if sec.rsize == 0 && sec.vsize > 0 {
            indicators.push(format!(
                "section '{}' has no raw data (unpacked at runtime)",
                sec.name
            ));
        }
    }

    for import in &pe.imports {
        let function = import.rsplit('!').next().unwrap_or(import);
        if anti_debug_imports().contains(&function) && !anti_debug.iter().any(|v| v == function) {
            anti_debug.push(function.to_string());
        }
        if import.contains("VBoxDispatch") {
            indicators.push(format!(
                "import '{}' -> VirtualBox API (VM detection target)",
                import
            ));
        }
        if import.contains("VMwareVMControl") {
            indicators.push(format!(
                "import '{}' -> VMware API (VM detection target)",
                import
            ));
        }
    }

    for sec in pe.sections.iter().filter(|sec| sec.exec) {
        let blob = section_data(&data, sec);
        let scan_len = blob.len().min(8192);
        let chunk = &blob[..scan_len];
        for idx in 0..chunk.len().saturating_sub(10) {
            if chunk[idx] == 0x68 && matches!(chunk[idx + 5], 0xE8 | 0xE9) {
                indicators.push(format!(
                    "VMP-style VM entry stub at section '{}'+0x{:X}",
                    sec.name, idx
                ));
                break;
            }
        }
        let rdtsc = count_bytes(chunk, b"\x0F\x31");
        if rdtsc >= 2 {
            indicators.push(format!(
                "RDTSC timing check ({rdtsc} instances in '{}')",
                sec.name
            ));
        }
        if contains_bytes(chunk, b"\xCD\x2D") {
            indicators.push(format!("INT 2D (SEH debug detection) in '{}'", sec.name));
        }
        if contains_bytes(chunk, b"\x65\x48\x8B\x04\x25\x60\x00\x00\x00")
            || contains_bytes(chunk, b"\x64\x48\x8B\x04\x25\x60\x00\x00\x00")
        {
            indicators.push(format!("PEB.BeingDebugged access in '{}'", sec.name));
        }
    }

    if let Some(last_end) = pe
        .sections
        .iter()
        .map(|sec| sec.raddr as usize + sec.rsize as usize)
        .max()
    {
        if last_end < data.len() {
            indicators.push(format!(
                "PE overlay: {} bytes after last section",
                data.len() - last_end
            ));
        }
    }

    Ok(Report {
        file: basename(path),
        size: data.len(),
        arch: if pe.pe64 { "x64" } else { "x86" }.to_string(),
        entry_rva: format!("0x{:X}", pe.entry_rva),
        sections: pe.sections.len(),
        imports: pe.imports.len(),
        protectors,
        indicators,
        anti_debug,
    })
}

fn print_report(report: &Report) {
    println!(
        "File: {} ({} bytes, {})",
        report.file, report.size, report.arch
    );
    println!("Entry: {}", report.entry_rva);
    println!("Sections: {}  Imports: {}", report.sections, report.imports);
    println!();
    if report.protectors.is_empty() {
        println!("No known protector sections found.");
    } else {
        println!("PROTECTORS DETECTED:");
        for protector in &report.protectors {
            println!("  + {} - {}", protector.name, protector.evidence);
        }
    }
    if !report.indicators.is_empty() {
        println!("\nINDICATORS:");
        for indicator in &report.indicators {
            println!("  - {indicator}");
        }
    }
    if !report.anti_debug.is_empty() {
        println!("\nANTI-DEBUG IMPORTS: {}", report.anti_debug.join(", "));
    }
}

fn main() {
    let args = Args::parse();
    let report = match analyze(&args.binary) {
        Ok(report) => report,
        Err(e) => {
            eprintln!("Error: {e}");
            std::process::exit(1);
        }
    };
    if args.json {
        println!("{}", serde_json::to_string_pretty(&report).unwrap());
        return;
    }
    print_report(&report);
}
