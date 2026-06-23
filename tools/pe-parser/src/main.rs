use pe_parser::{load_binary_data, parse_pe_bytes};
use std::env;
use std::path::Path;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <pe_file>", args[0]);
        std::process::exit(2);
    }

    let filepath = Path::new(&args[1]);
    let data = match load_binary_data(filepath) {
        Ok(d) => d,
        Err(e) => {
            let err_json = serde_json::json!({ "error": e });
            println!("{}", serde_json::to_string_pretty(&err_json).unwrap());
            std::process::exit(3);
        }
    };

    match parse_pe_bytes(&data) {
        Ok(parsed) => match serde_json::to_string_pretty(&parsed) {
            Ok(json) => println!("{}", json),
            Err(e) => {
                let err_json =
                    serde_json::json!({ "error": format!("JSON serialization error: {}", e) });
                println!("{}", serde_json::to_string_pretty(&err_json).unwrap());
                std::process::exit(4);
            }
        },
        Err(e) => {
            let err_json = serde_json::json!({ "error": e });
            println!("{}", serde_json::to_string_pretty(&err_json).unwrap());
            std::process::exit(1);
        }
    }
}
