use clap::Parser;
use pe_parser::api_index::{load_api_index, lookup_symbol, print_lookup_human};
use std::path::{Path, PathBuf};

#[derive(Parser)]
#[command(about = "Look up a Perception Enma API symbol")]
struct Args {
    symbol: String,
    #[arg(long)]
    lang: Option<String>,
    #[arg(long)]
    json: bool,
}

fn find_repo_root() -> Result<PathBuf, String> {
    let mut starts = Vec::new();
    if let Ok(exe) = std::env::current_exe() {
        starts.push(exe);
    }
    if let Ok(cwd) = std::env::current_dir() {
        starts.push(cwd);
    }
    for start in starts {
        for dir in start.ancestors() {
            if dir.join("knowledge").join("pcx-api-index.json").exists() {
                return Ok(dir.to_path_buf());
            }
        }
    }
    Err("could not locate repository root containing knowledge/pcx-api-index.json".to_string())
}

fn normalize_lang(lang: Option<&String>) -> Result<Option<&str>, String> {
    match lang.map(|s| s.as_str()) {
        None => Ok(None),
        Some("enma" | "em" | ".em") => Ok(Some("enma")),
        Some(other) => Err(format!(
            "unsupported --lang {other:?}; use enma"
        )),
    }
}

fn main() {
    let args = Args::parse();
    let repo_root = match find_repo_root() {
        Ok(root) => root,
        Err(e) => {
            eprintln!("ERROR: {e}");
            std::process::exit(2);
        }
    };
    let lang = match normalize_lang(args.lang.as_ref()) {
        Ok(lang) => lang,
        Err(e) => {
            eprintln!("ERROR: {e}");
            std::process::exit(2);
        }
    };
    let index = match load_api_index(Path::new(&repo_root)) {
        Ok(index) => index,
        Err(e) => {
            eprintln!("ERROR: {e}");
            std::process::exit(2);
        }
    };
    let result = lookup_symbol(&index, &args.symbol, lang);
    if args.json {
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
    } else {
        print_lookup_human(&result);
    }
    std::process::exit(if result.found { 0 } else { 1 });
}
