use clap::Parser;
use pe_parser::{load_binary_data, parse_pe_bytes, section_data};
use serde::Serialize;
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Analyze binary sections for packing, entropy, and anomalies")]
struct Args {
    binary: PathBuf,
    #[arg(long)]
    entropy: bool,
    #[arg(long)]
    json: bool,
}

#[derive(Serialize)]
struct SectionReport {
    name: String,
    virtual_addr: u32,
    virtual_size: u32,
    raw_addr: u32,
    raw_size: u32,
    entropy: f64,
    flags: Vec<String>,
    anomalies: Vec<String>,
}

#[derive(Serialize)]
struct Report {
    file: String,
    size: usize,
    arch: String,
    sections: Vec<SectionReport>,
    overlay_size: usize,
}

fn entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let mut freq = [0usize; 256];
    for byte in data {
        freq[*byte as usize] += 1;
    }
    let len = data.len() as f64;
    let mut ent = 0.0;
    for count in freq {
        if count > 0 {
            let p = count as f64 / len;
            ent -= p * p.log2();
        }
    }
    (ent * 1000.0).round() / 1000.0
}

fn basename(path: &PathBuf) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_else(|| path.to_str().unwrap_or(""))
        .to_string()
}

fn analyze(path: &PathBuf) -> Result<Report, String> {
    let data = load_binary_data(path)?;
    let pe = parse_pe_bytes(&data)?;
    let mut sections = Vec::new();

    for sec in &pe.sections {
        let blob = section_data(&data, sec);
        let ent = entropy(blob);
        let mut flags = Vec::new();
        if sec.chars & 0x00000020 != 0 {
            flags.push("CODE".to_string());
        }
        if sec.chars & 0x00000040 != 0 {
            flags.push("IDATA".to_string());
        }
        if sec.chars & 0x00000080 != 0 {
            flags.push("UDATA".to_string());
        }
        if sec.chars & 0x20000000 != 0 {
            flags.push("EXEC".to_string());
        }
        if sec.chars & 0x40000000 != 0 {
            flags.push("READ".to_string());
        }
        if sec.chars & 0x80000000 != 0 {
            flags.push("WRITE".to_string());
        }

        let mut anomalies = Vec::new();
        if ent > 7.0 && sec.rsize > 1024 {
            anomalies.push("HIGH ENTROPY (encrypted/compressed)".to_string());
        }
        if ent < 1.0 && sec.rsize > 1024 {
            anomalies.push("VERY LOW ENTROPY (padding/zeros)".to_string());
        }
        if sec.rsize == 0 && sec.vsize > 0 {
            anomalies.push("EMPTY ON DISK (runtime-unpacked)".to_string());
        }
        if sec.vsize > 0 && sec.rsize > 0 && sec.vsize > sec.rsize * 5 {
            anomalies.push(format!(
                "PACKED (VS/RS ratio: {:.1}x)",
                sec.vsize as f64 / sec.rsize as f64
            ));
        }
        if flags.iter().any(|f| f == "EXEC") && flags.iter().any(|f| f == "WRITE") {
            anomalies.push("WRITABLE+EXECUTABLE (SMC / packer)".to_string());
        }
        if sec.name.starts_with('.') && sec.name[1..].chars().all(|c| c.is_ascii_digit()) {
            anomalies.push("NUMERIC SECTION NAME (obfuscator)".to_string());
        }

        sections.push(SectionReport {
            name: sec.name.clone(),
            virtual_addr: sec.vaddr,
            virtual_size: sec.vsize,
            raw_addr: sec.raddr,
            raw_size: sec.rsize,
            entropy: ent,
            flags,
            anomalies,
        });
    }

    let overlay_size = sections
        .iter()
        .map(|sec| sec.raw_addr as usize + sec.raw_size as usize)
        .max()
        .filter(|end| *end < data.len())
        .map(|end| data.len() - end)
        .unwrap_or(0);

    Ok(Report {
        file: basename(path),
        size: data.len(),
        arch: if pe.pe64 { "x64" } else { "x86" }.to_string(),
        sections,
        overlay_size,
    })
}

fn print_report(report: &Report, show_entropy_bar: bool) {
    println!(
        "File: {} ({} bytes, {})",
        report.file, report.size, report.arch
    );
    println!();
    let hdr = format!(
        "{:<12} {:>10} {:>10} {:>10} {:>8} {:<24} Anomalies",
        "Name", "VAddr", "VSize", "RSize", "Entropy", "Flags"
    );
    println!("{hdr}");
    println!("{}", "-".repeat(hdr.len()));
    for sec in &report.sections {
        let mut ent = format!("{:.3}", sec.entropy);
        if show_entropy_bar {
            let bar_len = (sec.entropy * 3.0).floor() as usize;
            ent = format!(
                "{:.3} {}{}",
                sec.entropy,
                "#".repeat(bar_len.min(24)),
                ".".repeat(24usize.saturating_sub(bar_len.min(24)))
            );
        }
        println!(
            "{:<12} 0x{:08X} 0x{:08X} 0x{:08X} {:>8} {:<24} {}",
            sec.name,
            sec.virtual_addr,
            sec.virtual_size,
            sec.raw_size,
            ent,
            sec.flags.join(","),
            if sec.anomalies.is_empty() {
                "-".to_string()
            } else {
                sec.anomalies.join("; ")
            }
        );
    }
    if report.overlay_size > 0 {
        println!(
            "\nOverlay: {} bytes after last section",
            report.overlay_size
        );
    }
    let anomalous = report
        .sections
        .iter()
        .filter(|sec| !sec.anomalies.is_empty())
        .count();
    if anomalous > 0 {
        println!("\nWARN: {anomalous} section(s) with anomalies detected");
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
    print_report(&report, args.entropy);
}
