use serde_json::Value;
use std::collections::HashSet;
use std::fs;
use std::path::Path;

pub fn check_mcp_config(repo_root: &Path, json_out: bool, check: bool) -> i32 {
    let config_path = repo_root.join("mcp").join("perception-mcp-config.json");
    let doc_path = repo_root.join("docs").join("perception").join("mcp-api.md");

    if !config_path.exists() || !doc_path.exists() {
        eprintln!("ERROR: missing config or mcp-api.md");
        return 2;
    }

    let doc_txt = fs::read_to_string(&doc_path).unwrap_or_default();
    let doc_txt = doc_txt.split("\n# Agent Instructions").next().unwrap_or(&doc_txt);
    
    let re = regex::Regex::new(r"`((?:process|system|script)/[a-z_0-9]+)`").unwrap();
    let mut doc_tools = HashSet::new();
    for cap in re.captures_iter(doc_txt) {
        doc_tools.insert(cap[1].to_string());
    }

    let cfg_txt = fs::read_to_string(&config_path).unwrap_or_default();
    let cfg_json: Value = serde_json::from_str(&cfg_txt).unwrap_or_else(|_| serde_json::json!({}));
    
    let mut cfg_tools = HashSet::new();
    if let Some(servers) = cfg_json.get("mcpServers").and_then(|s| s.as_object()) {
        for srv in servers.values() {
            if let Some(tools) = srv.get("tools").and_then(|t| t.as_array()) {
                for t in tools {
                    if let Some(ts) = t.as_str() {
                        cfg_tools.insert(ts.to_string());
                    }
                }
            }
        }
    }

    let default_val = serde_json::json!({});
    let perception_srv = cfg_json
        .get("mcpServers")
        .and_then(|s| s.get("perception"))
        .unwrap_or(&default_val);

    let mut endpoint_errors = Vec::new();
    if let Some(url) = perception_srv.get("url").and_then(|u| u.as_str()) {
        if !url.starts_with("http://") && !url.starts_with("https://") {
            endpoint_errors.push(format!("url must be http(s), got {}", url));
        }
        if !url.trim_end_matches('/').ends_with("/mcp") {
            endpoint_errors.push("url path must be /mcp".to_string());
        }
    } else {
        endpoint_errors.push("missing string url".to_string());
    }

    if perception_srv.get("transport").and_then(|t| t.as_str()) != Some("http") {
        endpoint_errors.push("transport must be http".to_string());
    }
    if perception_srv.get("command").is_some() || perception_srv.get("args").is_some() {
        endpoint_errors.push("http MCP config must not include command/args".to_string());
    }

    let in_cfg_not_doc: Vec<String> = cfg_tools.difference(&doc_tools).cloned().collect();
    let in_doc_not_cfg: Vec<String> = doc_tools.difference(&cfg_tools).cloned().collect();

    let ok = endpoint_errors.is_empty() && in_cfg_not_doc.is_empty() && in_doc_not_cfg.is_empty();

    if json_out {
        let report = serde_json::json!({
            "endpoint_errors": endpoint_errors,
            "doc_tools": doc_tools.len(),
            "config_tools": cfg_tools.len(),
            "in_config_not_in_doc": in_cfg_not_doc,
            "in_doc_not_in_config": in_doc_not_cfg,
            "in_sync": ok,
        });
        println!("{}", serde_json::to_string_pretty(&report).unwrap());
    }

    if ok {
        if !json_out {
            println!("MCP config in sync with mcp-api.md: {} tools.", doc_tools.len());
        }
        return 0;
    }

    if !json_out {
        println!("MCP config OUT OF SYNC with docs/perception/mcp-api.md:");
        if !endpoint_errors.is_empty() {
            println!("  endpoint/config errors ({}):", endpoint_errors.len());
            for e in &endpoint_errors {
                println!("    ! {}", e);
            }
        }
        if !in_cfg_not_doc.is_empty() {
            println!("  in config but NOT in mcp-api.md ({}):", in_cfg_not_doc.len());
            for t in &in_cfg_not_doc {
                println!("    + {}", t);
            }
        }
        if !in_doc_not_cfg.is_empty() {
            println!("  in mcp-api.md but NOT in config ({}):", in_doc_not_cfg.len());
            for t in &in_doc_not_cfg {
                println!("    - {}", t);
            }
        }
    }
    
    if check || !json_out { 1 } else { 0 }
}
