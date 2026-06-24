use clap::Parser;
use pe_parser::{load_binary_data, parse_pe_bytes, section_data};
use serde::Serialize;
use std::collections::{BTreeMap, HashSet};
use std::path::PathBuf;

#[derive(Parser)]
#[command(about = "Scan a binary for anti-debug surfaces")]
struct Args {
    binary: PathBuf,
    #[arg(long)]
    json: bool,
    #[arg(long, default_value = "")]
    category: String,
}

#[derive(Serialize, Clone)]
struct Finding {
    category: String,
    detail: String,
    severity: String,
}

#[derive(Serialize)]
struct Report {
    binary: String,
    pe64: bool,
    findings: Vec<Finding>,
    summary: BTreeMap<String, usize>,
}

fn category_meta(cat: &str) -> (&'static str, &'static str) {
    match cat {
        "imports_direct" => ("Direct debugger-presence checks", "STRONG"),
        "imports_timing" => ("Timing-based detection imports", "INFO"),
        "imports_handler" => ("Exception-handler manipulation", "SUSPICIOUS"),
        "imports_window" => ("Window enumeration imports", "INFO"),
        "imports_process" => ("Process enumeration imports", "INFO"),
        "imports_threadctx" => ("Thread-context (HW BP) imports", "SUSPICIOUS"),
        "imports_env" => ("Debugger-environment probes", "INFO"),
        "peb" => ("PEB-relative byte patterns", "SUSPICIOUS"),
        "ntglobalflag" => ("NtGlobalFlag heap-flag check", "STRONG"),
        "timing" => ("RDTSC timing-pair patterns", "SUSPICIOUS"),
        "int2d" => ("INT 2D / INT 3 abuse patterns", "SUSPICIOUS"),
        "hwbp_context" => ("Debug-register CONTEXT manipulation", "STRONG"),
        "veh_chain" => ("VEH chain manipulation", "SUSPICIOUS"),
        "debugger_strings" => ("Known debugger process names", "STRONG"),
        "window_class_strings" => ("Known debugger window classes", "STRONG"),
        _ => ("Unknown", "INFO"),
    }
}

fn import_tables() -> Vec<(&'static str, &'static [&'static str])> {
    vec![
        (
            "imports_direct",
            &[
                "IsDebuggerPresent",
                "CheckRemoteDebuggerPresent",
                "NtQueryInformationProcess",
                "ZwQueryInformationProcess",
                "NtSetInformationThread",
                "ZwSetInformationThread",
                "DbgUiRemoteBreakin",
                "DbgBreakPoint",
                "DbgUserBreakPoint",
            ],
        ),
        (
            "imports_timing",
            &[
                "GetTickCount",
                "GetTickCount64",
                "QueryPerformanceCounter",
                "GetSystemTimeAsFileTime",
                "timeGetTime",
            ],
        ),
        (
            "imports_handler",
            &[
                "AddVectoredExceptionHandler",
                "RemoveVectoredExceptionHandler",
                "SetUnhandledExceptionFilter",
                "RaiseException",
            ],
        ),
        (
            "imports_window",
            &[
                "FindWindowA",
                "FindWindowW",
                "FindWindowExA",
                "FindWindowExW",
                "EnumWindows",
                "GetWindowTextA",
                "GetWindowTextW",
            ],
        ),
        (
            "imports_process",
            &[
                "CreateToolhelp32Snapshot",
                "Process32First",
                "Process32FirstW",
                "Process32Next",
                "Process32NextW",
                "EnumProcesses",
                "OpenProcess",
            ],
        ),
        (
            "imports_threadctx",
            &[
                "GetThreadContext",
                "SetThreadContext",
                "Wow64GetThreadContext",
                "Wow64SetThreadContext",
            ],
        ),
        (
            "imports_env",
            &[
                "OutputDebugStringA",
                "OutputDebugStringW",
                "BlockInput",
                "SwitchDesktop",
                "GetForegroundWindow",
            ],
        ),
    ]
}

fn debugger_process_strings() -> &'static [&'static str] {
    &[
        "ollydbg.exe",
        "x32dbg.exe",
        "x64dbg.exe",
        "ida.exe",
        "ida64.exe",
        "idaq.exe",
        "idaq64.exe",
        "idaw.exe",
        "idaw64.exe",
        "windbg.exe",
        "ghidra",
        "cheatengine.exe",
        "cheatengine-x86_64.exe",
        "processhacker.exe",
        "procexp.exe",
        "procmon.exe",
        "fiddler.exe",
        "httpdebuggerui.exe",
        "wireshark.exe",
        "apimonitor",
        "scylla",
        "pe-sieve",
        "lordpe.exe",
        "immunitydebugger.exe",
        "binaryninja",
    ]
}

fn debugger_window_classes() -> &'static [&'static str] {
    &[
        "OLLYDBG",
        "WinDbgFrameClass",
        "Zeta Debugger",
        "Rock Debugger",
        "ImmunityDebugger",
        "IDA View",
        "IDA Window",
    ]
}

fn contains_bytes(haystack: &[u8], needle: &[u8]) -> bool {
    needle.len() <= haystack.len() && haystack.windows(needle.len()).any(|w| w == needle)
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

fn wide_ascii(text: &str) -> Vec<u8> {
    let mut out = Vec::with_capacity(text.len() * 2);
    for byte in text.as_bytes() {
        out.push(*byte);
        out.push(0);
    }
    out
}

fn imports(parsed: &pe_parser::ParsedPE) -> Vec<(String, String)> {
    parsed
        .imports
        .iter()
        .filter_map(|imp| {
            imp.split_once('!')
                .map(|(dll, func)| (dll.to_string(), func.to_string()))
        })
        .collect()
}

fn detect_imports(imports: &[(String, String)]) -> Vec<Finding> {
    let mut out = Vec::new();
    for (cat, names) in import_tables() {
        let mut hits = imports
            .iter()
            .filter(|(_, func)| names.contains(&func.as_str()))
            .map(|(dll, func)| format!("{dll}!{func}"))
            .collect::<Vec<_>>();
        hits.sort();
        hits.dedup();
        if !hits.is_empty() {
            out.push(Finding {
                category: cat.to_string(),
                detail: hits.join(", "),
                severity: category_meta(cat).1.to_string(),
            });
        }
    }
    out
}

fn detect_peb_patterns(data: &[u8], parsed: &pe_parser::ParsedPE) -> Vec<Finding> {
    let patterns: [(&[u8], &str); 3] = [
        (b"\x64\xA1\x30\x00\x00\x00", "fs:[30h]  (32-bit PEB)"),
        (
            b"\x65\x48\x8B\x04\x25\x60\x00\x00\x00",
            "gs:[60h]  (64-bit PEB)",
        ),
        (
            b"\x65\x48\x8B\x0C\x25\x60\x00\x00\x00",
            "gs:[60h]  (64-bit PEB, RCX form)",
        ),
    ];
    let mut out = Vec::new();
    for sec in parsed
        .sections
        .iter()
        .filter(|sec| sec.exec && sec.rsize > 0)
    {
        let blob = section_data(data, sec);
        for (pat, label) in patterns {
            for idx in find_all(blob, pat) {
                out.push(Finding {
                    category: "peb".to_string(),
                    detail: format!(
                        "{label} at {}+0x{:X} (rva 0x{:X})",
                        sec.name,
                        idx,
                        sec.vaddr + idx as u32
                    ),
                    severity: category_meta("peb").1.to_string(),
                });
                let window = &blob[idx..blob.len().min(idx + 64)];
                if window
                    .windows(3)
                    .any(|w| w[0] == 0x83 && (0xF8..=0xFF).contains(&w[1]) && w[2] == 0x70)
                {
                    out.push(Finding {
                        category: "ntglobalflag".to_string(),
                        detail: format!(
                            "PEB+NtGlobalFlag(0x70) check near {}+0x{:X}",
                            sec.name, idx
                        ),
                        severity: category_meta("ntglobalflag").1.to_string(),
                    });
                }
            }
        }
    }
    out
}

fn detect_rdtsc_pairs(data: &[u8], parsed: &pe_parser::ParsedPE) -> Vec<Finding> {
    let mut out = Vec::new();
    for sec in parsed
        .sections
        .iter()
        .filter(|sec| sec.exec && sec.rsize > 0)
    {
        let blob = section_data(data, sec);
        let hits = find_all(blob, b"\x0F\x31");
        for pair in hits.windows(2) {
            let (a, b) = (pair[0], pair[1]);
            if b > a && b - a <= 256 {
                out.push(Finding {
                    category: "timing".to_string(),
                    detail: format!(
                        "RDTSC pair at {}+0x{:X} -> +0x{:X} (gap {}B)",
                        sec.name,
                        a,
                        b,
                        b - a
                    ),
                    severity: category_meta("timing").1.to_string(),
                });
            }
        }
    }
    out
}

fn detect_int_abuse(data: &[u8], parsed: &pe_parser::ParsedPE) -> Vec<Finding> {
    let mut out = Vec::new();
    for sec in parsed
        .sections
        .iter()
        .filter(|sec| sec.exec && sec.rsize > 0)
    {
        let blob = section_data(data, sec);
        for idx in find_all(blob, b"\xCD\x2D") {
            out.push(Finding {
                category: "int2d".to_string(),
                detail: format!("INT 2D at {}+0x{:X}", sec.name, idx),
                severity: category_meta("int2d").1.to_string(),
            });
        }
        for idx in 0..blob.len() {
            let ret_len = if blob[idx] == 0xC3 {
                1
            } else if blob[idx] == 0xC2 && idx + 2 < blob.len() {
                3
            } else {
                0
            };
            if ret_len == 0 {
                continue;
            }
            let mut cc = 0usize;
            let mut j = idx + ret_len;
            while j < blob.len() && blob[j] == 0xCC {
                cc += 1;
                j += 1;
            }
            if cc >= 12 {
                out.push(Finding {
                    category: "int2d".to_string(),
                    detail: format!(
                        "long INT 3 fill after RET at {}+0x{:X}",
                        sec.name,
                        idx + ret_len
                    ),
                    severity: "INFO".to_string(),
                });
            }
        }
    }
    out
}

fn detect_hwbp_context(
    data: &[u8],
    parsed: &pe_parser::ParsedPE,
    imports: &[(String, String)],
) -> Vec<Finding> {
    let funcs: HashSet<_> = imports.iter().map(|(_, f)| f.as_str()).collect();
    if ![
        "GetThreadContext",
        "SetThreadContext",
        "Wow64GetThreadContext",
        "Wow64SetThreadContext",
    ]
    .iter()
    .any(|f| funcs.contains(f))
    {
        return Vec::new();
    }
    let needles: [(&[u8], &str); 2] = [
        (b"\x10\x00\x01\x00", "CONTEXT_DEBUG_REGISTERS (x86)"),
        (b"\x10\x00\x10\x00", "CONTEXT_DEBUG_REGISTERS (x64)"),
    ];
    let mut out = Vec::new();
    for sec in parsed
        .sections
        .iter()
        .filter(|sec| sec.exec && sec.rsize > 0)
    {
        let blob = section_data(data, sec);
        for (pat, label) in needles {
            if let Some(idx) = find_all(blob, pat).first().copied() {
                out.push(Finding {
                    category: "hwbp_context".to_string(),
                    detail: format!(
                        "{label} literal at {}+0x{:X}; paired with thread-context import",
                        sec.name, idx
                    ),
                    severity: category_meta("hwbp_context").1.to_string(),
                });
            }
        }
    }
    out
}

fn detect_veh_chain(imports: &[(String, String)]) -> Vec<Finding> {
    let funcs: HashSet<_> = imports.iter().map(|(_, f)| f.as_str()).collect();
    if funcs.contains("AddVectoredExceptionHandler")
        && funcs.contains("RemoveVectoredExceptionHandler")
    {
        vec![Finding {
            category: "veh_chain".to_string(),
            detail:
                "AddVectoredExceptionHandler + RemoveVectoredExceptionHandler (handler-shuffle pattern)"
                    .to_string(),
            severity: category_meta("veh_chain").1.to_string(),
        }]
    } else {
        Vec::new()
    }
}

fn detect_debugger_strings(data: &[u8]) -> Vec<Finding> {
    let lower = data
        .iter()
        .map(|b| b.to_ascii_lowercase())
        .collect::<Vec<_>>();
    let mut out = Vec::new();
    for name in debugger_process_strings() {
        if contains_bytes(&lower, name.as_bytes()) {
            out.push(Finding {
                category: "debugger_strings".to_string(),
                detail: format!("string ref: \"{name}\""),
                severity: category_meta("debugger_strings").1.to_string(),
            });
        }
        let wide = wide_ascii(name);
        if contains_bytes(&lower, &wide) {
            out.push(Finding {
                category: "debugger_strings".to_string(),
                detail: format!("wstring ref: \"{name}\""),
                severity: category_meta("debugger_strings").1.to_string(),
            });
        }
    }
    for class_name in debugger_window_classes() {
        if contains_bytes(data, class_name.as_bytes()) {
            out.push(Finding {
                category: "window_class_strings".to_string(),
                detail: format!("window class: \"{class_name}\""),
                severity: category_meta("window_class_strings").1.to_string(),
            });
        }
        let wide = wide_ascii(class_name);
        if contains_bytes(data, &wide) {
            out.push(Finding {
                category: "window_class_strings".to_string(),
                detail: format!("window class (wide): \"{class_name}\""),
                severity: category_meta("window_class_strings").1.to_string(),
            });
        }
    }
    out
}

fn scan(path: &PathBuf, want: Option<HashSet<String>>) -> Result<Report, String> {
    let data = load_binary_data(path)?;
    let parsed = parse_pe_bytes(&data)?;
    let imports = imports(&parsed);
    let mut findings = Vec::new();
    findings.extend(detect_imports(&imports));
    findings.extend(detect_peb_patterns(&data, &parsed));
    findings.extend(detect_rdtsc_pairs(&data, &parsed));
    findings.extend(detect_int_abuse(&data, &parsed));
    findings.extend(detect_hwbp_context(&data, &parsed, &imports));
    findings.extend(detect_veh_chain(&imports));
    findings.extend(detect_debugger_strings(&data));
    if let Some(want) = want {
        findings.retain(|finding| want.contains(&finding.category));
    }
    let mut summary = BTreeMap::from([
        ("INFO".to_string(), 0usize),
        ("STRONG".to_string(), 0usize),
        ("SUSPICIOUS".to_string(), 0usize),
    ]);
    for finding in &findings {
        *summary.entry(finding.severity.clone()).or_insert(0) += 1;
    }
    Ok(Report {
        binary: path.display().to_string(),
        pe64: parsed.pe64,
        findings,
        summary,
    })
}

fn print_report(report: &Report) {
    println!(
        "File: {}  ({})",
        report.binary,
        if report.pe64 { "x64" } else { "x86" }
    );
    let mut by_cat: BTreeMap<&str, Vec<&Finding>> = BTreeMap::new();
    for finding in &report.findings {
        by_cat
            .entry(finding.category.as_str())
            .or_default()
            .push(finding);
    }
    if by_cat.is_empty() {
        println!("\nNo anti-debug surfaces detected.");
        return;
    }
    for (cat, items) in by_cat {
        println!(
            "\n[{cat}]  {}  ({} finding{})",
            category_meta(cat).0,
            items.len(),
            if items.len() == 1 { "" } else { "s" }
        );
        for item in items {
            println!("  {:<10}  {}", item.severity, item.detail);
        }
    }
    println!(
        "\nSummary: {} STRONG, {} SUSPICIOUS, {} INFO",
        report.summary.get("STRONG").unwrap_or(&0),
        report.summary.get("SUSPICIOUS").unwrap_or(&0),
        report.summary.get("INFO").unwrap_or(&0)
    );
}

fn main() {
    let args = Args::parse();
    let want = if args.category.trim().is_empty() {
        None
    } else {
        Some(
            args.category
                .split(',')
                .map(|cat| cat.trim().to_string())
                .filter(|cat| !cat.is_empty())
                .collect::<HashSet<_>>(),
        )
    };
    let report = match scan(&args.binary, want) {
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
