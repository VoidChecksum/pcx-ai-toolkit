use pe_parser::mcp_schema::{all_tools, McpError};
use std::collections::BTreeSet;
#[test]
fn error_codes() {
    assert_eq!(McpError::PERMISSION_DENIED, -32001);
    assert_eq!(McpError::STALE_HANDLE, -32002);
}
fn documented_tool_names() -> BTreeSet<String> {
    let p = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join("docs/perception/mcp-api.md");
    let docs = std::fs::read_to_string(p).unwrap();
    let sec = docs
        .split("## Tools")
        .nth(1)
        .unwrap()
        .split("## Example")
        .next()
        .unwrap()
        .to_string();
    sec.split('`')
        .skip(1)
        .step_by(2)
        .filter(|s| {
            s.starts_with("process/") || s.starts_with("system/") || s.starts_with("script/")
        })
        .map(|s| s.to_string())
        .collect()
}
#[test]
fn mirrors_docs() {
    let d = documented_tool_names();
    let m = all_tools()
        .iter()
        .map(|t| t.name.to_string())
        .collect::<BTreeSet<_>>();
    assert_eq!(d.len(), 59);
    assert_eq!(m, d);
}
#[test]
fn captures_caps() {
    let t = all_tools()
        .iter()
        .find(|t| t.name == "process/find_string_refs")
        .unwrap();
    assert!(t.notes.contains(&"code_hit_cap=4096"));
}
