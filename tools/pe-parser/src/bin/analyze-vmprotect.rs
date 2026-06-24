use clap::Parser;
use pe_parser::{load_binary_data, parse_pe_bytes, section_data};
use serde::Serialize;
use std::path::{Path, PathBuf};
use std::process::Command;

#[derive(Parser)]
#[command(about = "Analyze VMProtect-protected binaries and recommend workflows")]
struct Args {
    binary: PathBuf,
    #[arg(long)]
    json: bool,
    #[arg(long = "run-vmemu")]
    run_vmemu: bool,
    #[arg(long, default_value = "unpacked.bin")]
    out: PathBuf,
}

#[derive(Serialize)]
struct SectionInfo {
    name: String,
    virtual_size: u32,
    virtual_addr: u32,
    raw_size: u32,
    raw_addr: u32,
    exec: bool,
    is_vmp: bool,
    entropy: Option<f64>,
}

#[derive(Serialize)]
struct VmEntry {
    rva: String,
    file_offset: u32,
    section: String,
    #[serde(rename = "type")]
    entry_type: String,
}

#[derive(Serialize)]
struct Indicator {
    pattern: String,
    description: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    section: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    file_offset: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    rva: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    value: Option<Vec<String>>,
}

#[derive(Serialize)]
struct Recommendation {
    tool: String,
    use_case: String,
    note: String,
    url: String,
}

#[derive(Serialize)]
struct VmemuResult {
    #[serde(skip_serializing_if = "Option::is_none")]
    returncode: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stdout: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stderr: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    output_file: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Serialize)]
struct Report {
    file: String,
    size: usize,
    arch: String,
    vmprotect_detected: bool,
    version_hint: String,
    sections: Vec<SectionInfo>,
    vm_entries: Vec<VmEntry>,
    indicators: Vec<Indicator>,
    recommendations: Vec<Recommendation>,
    vmemu_result: Option<VmemuResult>,
}

fn basename(path: &PathBuf) -> String {
    path.file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_else(|| path.to_str().unwrap_or(""))
        .to_string()
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
    (ent * 100.0).round() / 100.0
}

fn find_all(blob: &[u8], pat: &[u8]) -> Vec<usize> {
    if pat.is_empty() || pat.len() > blob.len() {
        return Vec::new();
    }
    blob.windows(pat.len())
        .enumerate()
        .filter_map(|(idx, w)| (w == pat).then_some(idx))
        .collect()
}

fn recommendations() -> Vec<Recommendation> {
    vec![
        Recommendation {
            tool: "backengineering/vmp2".to_string(),
            use_case: "VMProtect 2.x unpacking and VM bytecode analysis".to_string(),
            note: "Use vmemu to unpack and produce .vmp2 CFG; vmdevirt recompiles (experimental)."
                .to_string(),
            url: "https://github.com/backengineering/vmp2".to_string(),
        },
        Recommendation {
            tool: "x64dbg + ScyllaHide".to_string(),
            use_case: "Anti-debug bypass for live VMProtect debugging".to_string(),
            note: "Enable all ScyllaHide options, set VirtualProtect breakpoint to reach OEP."
                .to_string(),
            url: "https://github.com/x64dbg/ScyllaHide".to_string(),
        },
        Recommendation {
            tool: "NoVmp".to_string(),
            use_case: "VMProtect 3.x static devirtualization".to_string(),
            note: "Lifts VMP bytecode to LLVM IR; requires target RVA.".to_string(),
            url: "https://github.com/can1357/NoVmp".to_string(),
        },
        Recommendation {
            tool: "vtil / VTIL-Core".to_string(),
            use_case: "Generic VM lifting and optimization IR".to_string(),
            note: "Alternative to LLVM IR for VM-specific semantics.".to_string(),
            url: "https://github.com/vtil-project/VTIL-Core".to_string(),
        },
    ]
}

fn find_tool(name: &str) -> Option<PathBuf> {
    let candidates = std::env::var_os("PATH")?;
    for dir in std::env::split_paths(&candidates) {
        let raw = dir.join(name);
        if raw.is_file() {
            return Some(raw);
        }
        let exe = dir.join(format!("{name}.exe"));
        if exe.is_file() {
            return Some(exe);
        }
    }
    None
}

fn run_vmemu(binary: &Path, out: &Path) -> VmemuResult {
    let Some(vmemu) = find_tool("vmemu") else {
        return VmemuResult {
            returncode: None,
            stdout: None,
            stderr: None,
            output_file: None,
            error: Some(
                "vmemu not found in PATH. Add it to PATH or place next to this script.".to_string(),
            ),
        };
    };
    match Command::new(vmemu)
        .arg("--bin")
        .arg(binary)
        .arg("--unpack")
        .arg("--out")
        .arg(out)
        .output()
    {
        Ok(output) => VmemuResult {
            returncode: output.status.code(),
            stdout: Some(String::from_utf8_lossy(&output.stdout).into_owned()),
            stderr: Some(String::from_utf8_lossy(&output.stderr).into_owned()),
            output_file: out.exists().then(|| out.display().to_string()),
            error: None,
        },
        Err(e) => VmemuResult {
            returncode: None,
            stdout: None,
            stderr: None,
            output_file: None,
            error: Some(e.to_string()),
        },
    }
}

fn analyze(args: &Args) -> Result<Report, String> {
    let data = load_binary_data(&args.binary)?;
    let pe = parse_pe_bytes(&data)?;
    let mut sections = Vec::new();
    let mut vm_entries = Vec::new();
    let mut indicators = Vec::new();

    for sec in &pe.sections {
        let raw_name = sec.name.as_bytes();
        let is_vmp = [".vmp0", ".vmp1", ".vmp2", ".vmp3", ".vmp4"]
            .iter()
            .any(|needle| {
                raw_name
                    .windows(needle.len())
                    .any(|w| w == needle.as_bytes())
            });
        let blob = section_data(&data, sec);
        sections.push(SectionInfo {
            name: sec.name.clone(),
            virtual_size: sec.vsize,
            virtual_addr: sec.vaddr,
            raw_size: sec.rsize,
            raw_addr: sec.raddr,
            exec: sec.exec,
            is_vmp,
            entropy: (!blob.is_empty()).then(|| entropy(blob)),
        });
    }

    for sec in pe.sections.iter().filter(|sec| sec.exec && sec.rsize > 0) {
        let blob = section_data(&data, sec);
        let patterns: [(&str, &[u8], &str); 5] = [
            ("rdtsc", b"\x0F\x31", "RDTSC timing check"),
            ("int2d", b"\xCD\x2D", "INT 2D SEH debug detection"),
            (
                "peb_debug_x64",
                b"\x65\x48\x8B\x04\x25\x60\x00\x00\x00",
                "PEB.BeingDebugged access (x64)",
            ),
            (
                "peb_debug_x86",
                b"\x64\xA1\x30\x00\x00\x00",
                "PEB.BeingDebugged access (x86)",
            ),
            ("cpuid", b"\x0F\xA2", "CPUID (hypervisor/VM detection)"),
        ];
        for (name, pat, desc) in patterns {
            for hit in find_all(blob, pat).into_iter().take(5) {
                indicators.push(Indicator {
                    pattern: name.to_string(),
                    description: desc.to_string(),
                    section: Some(sec.name.clone()),
                    file_offset: Some(sec.raddr + hit as u32),
                    rva: Some(format!("0x{:X}", sec.vaddr + hit as u32)),
                    value: None,
                });
            }
        }
        for idx in 0..blob.len().saturating_sub(6) {
            if blob[idx] == 0x68 && matches!(blob[idx + 5], 0xE8 | 0xE9) {
                let kind = if blob[idx + 5] == 0xE8 { "call" } else { "jmp" };
                if vm_entries.len() < 10 {
                    vm_entries.push(VmEntry {
                        rva: format!("0x{:X}", sec.vaddr + idx as u32),
                        file_offset: sec.raddr + idx as u32,
                        section: sec.name.clone(),
                        entry_type: format!("push_imm32;{kind}"),
                    });
                }
            }
        }
    }

    let vmp_dlls: Vec<String> = pe
        .imports
        .iter()
        .filter_map(|imp| imp.split_once('!').map(|(dll, _)| dll.to_string()))
        .filter(|dll| dll.contains("vmprotect"))
        .collect();
    if !vmp_dlls.is_empty() {
        indicators.push(Indicator {
            pattern: "vmp_dll_name".to_string(),
            description: "DLL name references VMProtect".to_string(),
            section: None,
            file_offset: None,
            rva: None,
            value: Some(vmp_dlls),
        });
    }

    let section_names: Vec<_> = sections.iter().map(|sec| sec.name.as_str()).collect();
    let version_hint = if section_names.contains(&".vmp2") {
        "likely VMProtect 2.x (vmp2 tooling applicable)"
    } else if section_names.contains(&".vmp3") {
        "likely VMProtect 3.x (NoVmp / VTIL toolchain recommended)"
    } else if section_names.contains(&".vmp0") || section_names.contains(&".vmp1") {
        "likely VMProtect 1.x or 2.x"
    } else {
        "VMProtect variant unknown (section names absent or non-standard)"
    };

    Ok(Report {
        file: basename(&args.binary),
        size: data.len(),
        arch: if pe.pe64 { "x64" } else { "x86" }.to_string(),
        vmprotect_detected: sections.iter().any(|sec| sec.is_vmp),
        version_hint: version_hint.to_string(),
        sections,
        vm_entries,
        indicators,
        recommendations: recommendations(),
        vmemu_result: args.run_vmemu.then(|| run_vmemu(&args.binary, &args.out)),
    })
}

fn print_report(report: &Report) {
    println!(
        "File: {} ({} bytes, {})",
        report.file, report.size, report.arch
    );
    println!(
        "VMProtect detected: {}",
        if report.vmprotect_detected {
            "YES"
        } else {
            "NO"
        }
    );
    println!("Version hint: {}", report.version_hint);
    println!("\nSections:");
    for sec in &report.sections {
        println!(
            "  {:5} {:10} VS=0x{:08X} RS=0x{:08X} entropy={:?}",
            if sec.is_vmp { "[VMP]" } else { "" },
            sec.name,
            sec.virtual_size,
            sec.raw_size,
            sec.entropy
        );
    }
    if !report.vm_entries.is_empty() {
        println!("\nVM entry stubs found: {}", report.vm_entries.len());
        for entry in report.vm_entries.iter().take(10) {
            println!(
                "  - {} ({}) in {}",
                entry.rva, entry.entry_type, entry.section
            );
        }
    }
    if !report.indicators.is_empty() {
        println!("\nIndicators:");
        for indicator in &report.indicators {
            println!(
                "  - {} at {} in {}",
                indicator.description,
                indicator.rva.as_deref().unwrap_or("N/A"),
                indicator.section.as_deref().unwrap_or("N/A")
            );
        }
    }
    println!("\nRecommendations:");
    for rec in &report.recommendations {
        println!("  - {} - {}", rec.tool, rec.use_case);
        println!("    {}", rec.note);
        println!("    {}", rec.url);
    }
}

fn main() {
    let args = Args::parse();
    let report = match analyze(&args) {
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
