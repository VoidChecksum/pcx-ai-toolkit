use clap::Parser;
use pe_parser::format_byte_pattern;
use serde::Serialize;

const FORMATS: &[&str] = &[
    "ida", "ghidra", "x64dbg", "ce", "enma", "cstyle", "bytes", "sig_mask",
];

#[derive(Parser)]
#[command(about = "Convert byte patterns between RE-tool formats")]
struct Args {
    #[arg(long = "from")]
    src: String,
    #[arg(long = "to")]
    dst: String,
    #[arg(long)]
    pat: String,
    #[arg(long)]
    mask: Option<String>,
    #[arg(long)]
    json: bool,
}

#[derive(Serialize)]
struct JsonOut {
    #[serde(rename = "from")]
    src: String,
    length: usize,
    wildcards: usize,
    normalized: Vec<Option<u8>>,
    formats: std::collections::BTreeMap<String, String>,
}

fn strip_quotes(s: &str) -> &str {
    let s = s.trim();
    if s.len() >= 2 {
        let first = s.as_bytes()[0];
        let last = s.as_bytes()[s.len() - 1];
        if (first == b'"' || first == b'\'') && first == last {
            return &s[1..s.len() - 1];
        }
    }
    s
}

fn hex_byte(tok: &str) -> Result<u8, String> {
    if tok.len() != 2 || !tok.chars().all(|c| c.is_ascii_hexdigit()) {
        return Err(format!("invalid hex byte {tok:?} (need 2 hex digits)"));
    }
    u8::from_str_radix(tok, 16).map_err(|_| format!("invalid hex byte {tok:?}"))
}

fn parse_tokens(pat: &str) -> Result<Vec<Option<u8>>, String> {
    let mut out = Vec::new();
    for tok in pat.split_whitespace() {
        if matches!(tok, "?" | "??" | "..") {
            out.push(None);
        } else {
            out.push(Some(hex_byte(tok)?));
        }
    }
    if out.is_empty() {
        return Err("empty pattern".to_string());
    }
    Ok(out)
}

fn parse_escapes(pat: &str) -> Result<Vec<u8>, String> {
    let raw = pat.trim();
    let raw = if raw.starts_with('b') || raw.starts_with('B') {
        &raw[1..]
    } else {
        raw
    };
    let s = strip_quotes(raw);
    let bytes = s.as_bytes();
    let mut out = Vec::new();
    let mut i = 0usize;
    while i < bytes.len() {
        if i + 3 < bytes.len() && bytes[i] == b'\\' && matches!(bytes[i + 1], b'x' | b'X') {
            out.push(hex_byte(&s[i + 2..i + 4])?);
            i += 4;
        } else {
            return Err(format!(
                "unexpected char {:?} in byte literal",
                bytes[i] as char
            ));
        }
    }
    if out.is_empty() {
        return Err("empty pattern".to_string());
    }
    Ok(out)
}

fn apply_mask(bytes: Vec<u8>, mask: Option<&String>) -> Result<Vec<Option<u8>>, String> {
    let Some(mask) = mask else {
        return Err("this --from format requires --mask".to_string());
    };
    let mask = strip_quotes(mask);
    if mask.len() != bytes.len() {
        return Err(format!(
            "mask length {} != byte count {}",
            mask.len(),
            bytes.len()
        ));
    }
    bytes
        .into_iter()
        .zip(mask.chars())
        .map(|(byte, m)| match m {
            'x' => Ok(Some(byte)),
            '?' | '.' => Ok(None),
            _ => Err(format!("invalid mask char {m:?} (use x, ?, or .)")),
        })
        .collect()
}

fn to_norm(fmt: &str, pat: &str, mask: Option<&String>) -> Result<Vec<Option<u8>>, String> {
    match fmt {
        "enma" => parse_tokens(strip_quotes(pat)),
        "ida" | "ghidra" | "x64dbg" | "ce" => parse_tokens(pat),
        "cstyle" | "bytes" => apply_mask(parse_escapes(pat)?, mask),
        "sig_mask" => apply_mask(
            pat.split_whitespace()
                .map(hex_byte)
                .collect::<Result<Vec<_>, _>>()?,
            mask,
        ),
        _ => Err(format!("unknown format {fmt:?}")),
    }
}

fn tokens(norm: &[Option<u8>], wild: &str, lower: bool) -> String {
    norm.iter()
        .map(|byte| match byte {
            Some(byte) if lower => format!("{byte:02x}"),
            Some(byte) => format!("{byte:02X}"),
            None => wild.to_string(),
        })
        .collect::<Vec<_>>()
        .join(" ")
}

fn escapes(norm: &[Option<u8>]) -> String {
    norm.iter()
        .map(|byte| match byte {
            Some(byte) => format!("\\x{byte:02X}"),
            None => "\\x00".to_string(),
        })
        .collect::<String>()
}

fn mask_str(norm: &[Option<u8>]) -> String {
    norm.iter()
        .map(|byte| if byte.is_some() { 'x' } else { '?' })
        .collect()
}

fn emit(fmt: &str, norm: &[Option<u8>]) -> Result<String, String> {
    match fmt {
        "ida" => Ok(tokens(norm, "?", false)),
        "ghidra" => Ok(tokens(norm, "..", true)),
        "x64dbg" | "ce" => Ok(format_byte_pattern(norm)),
        "enma" => Ok(format!("\"{}\"", format_byte_pattern(norm))),
        "cstyle" => Ok(format!("\"{}\" \"{}\"", escapes(norm), mask_str(norm))),
        "bytes" => Ok(format!(
            "b\"{}\"  # mask: {}",
            escapes(norm),
            mask_str(norm)
        )),
        "sig_mask" => Ok(format!("{}\n{}", tokens(norm, "00", false), mask_str(norm))),
        _ => Err(format!("unknown format {fmt:?}")),
    }
}

fn main() {
    let args = Args::parse();
    if !FORMATS.contains(&args.src.as_str()) {
        eprintln!("error: unknown --from {:?}", args.src);
        std::process::exit(1);
    }
    if args.dst != "all" && !FORMATS.contains(&args.dst.as_str()) {
        eprintln!("error: unknown --to {:?}", args.dst);
        std::process::exit(1);
    }
    let norm = match to_norm(&args.src, &args.pat, args.mask.as_ref()) {
        Ok(norm) => norm,
        Err(e) => {
            eprintln!("error: {e}");
            std::process::exit(1);
        }
    };
    let targets = if args.dst == "all" {
        FORMATS.to_vec()
    } else {
        vec![args.dst.as_str()]
    };
    let mut rendered = std::collections::BTreeMap::new();
    for target in targets {
        rendered.insert(target.to_string(), emit(target, &norm).unwrap());
    }
    if args.json {
        println!(
            "{}",
            serde_json::to_string_pretty(&JsonOut {
                src: args.src,
                length: norm.len(),
                wildcards: norm.iter().filter(|b| b.is_none()).count(),
                normalized: norm,
                formats: rendered,
            })
            .unwrap()
        );
        return;
    }
    if args.dst != "all" {
        println!("{}", rendered.get(&args.dst).unwrap());
        return;
    }
    let width = FORMATS.iter().map(|f| f.len()).max().unwrap_or(0) + 2;
    for fmt in FORMATS {
        let value = rendered.get(*fmt).unwrap();
        let mut lines = value.lines();
        if let Some(first) = lines.next() {
            println!("{fmt:<width$}{first}");
        }
        for line in lines {
            println!("{:<width$}{line}", "");
        }
    }
}
