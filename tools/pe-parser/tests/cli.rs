use std::{
    fs,
    io::Write,
    process::{Command, Stdio},
};

#[test]
fn native_counts_json_does_not_need_python() {
    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["counts", "--json"])
        .env("PATH", "")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let json: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert!(json["docs"].as_u64().unwrap() > 0);
    assert!(json["native_tools"].as_u64().unwrap() > 0);
}

#[test]
fn native_build_provenance_check_does_not_need_python() {
    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["build-provenance", "--check"])
        .env("PATH", "")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("PROVENANCE.json in sync"));
}

#[test]
fn native_build_provenance_json_reports_counts() {
    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["build-provenance", "--json"])
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let json: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(json["source"], "rust");
    assert!(json["count"].as_u64().unwrap() > 80);
    assert!(json["drift_checkable"].as_u64().unwrap() > 50);
    assert!(json["unmapped"].as_array().unwrap().len() > 0);
}
#[test]
fn verify_project_json_reports_summary() {
    let dir = std::env::temp_dir().join("pcx_verify_json_project");
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("main.em"), "int64 main(){return 1;}\n").unwrap();

    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args([
            "verify-project",
            dir.to_str().unwrap(),
            "--json",
            "--allow-placeholders",
            "--allow-unverified",
        ])
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let json: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(json["ok"], true);
    assert_eq!(json["scripts"], 1);
    assert_eq!(json["findings"].as_array().unwrap().len(), 0);

    let _ = fs::remove_dir_all(dir);
}

#[test]
fn mcp_reads_json_request_from_stdin() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .arg("mcp")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(br#"{"id":1,"method":"overview","params":{}}"#)
        .unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let json: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(json["id"], 1);
    assert_eq!(json["result"]["name"], "pcx-ai-toolkit");
    assert_eq!(
        json["result"]["authorized_use"]["scope"],
        "owned-lab-ctf-or-authorized-research"
    );
}

#[test]
fn mcp_accepts_line_delimited_requests() {
    let mut child = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .arg("mcp")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(
            b"{\"id\":1,\"method\":\"ping\",\"params\":{}}\n{\"method\":\"notifications/initialized\",\"params\":{}}\n{\"id\":2,\"method\":\"overview\",\"params\":{}}\n",
        )
        .unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    let lines = String::from_utf8_lossy(&out.stdout)
        .lines()
        .map(|line| serde_json::from_str::<serde_json::Value>(line).unwrap())
        .collect::<Vec<_>>();
    assert_eq!(lines.len(), 2);
    assert_eq!(lines[0]["id"], 1);
    assert_eq!(lines[0]["result"], serde_json::json!({}));
    assert_eq!(lines[1]["id"], 2);
    assert_eq!(lines[1]["result"]["name"], "pcx-ai-toolkit");
}

#[test]
fn mcp_supports_standard_tools_call() {
    let response = mcp_call(
        "tools/call",
        serde_json::json!({"name":"api_lookup","arguments":{"symbol":"draw_text","language":"enma"}}),
    );
    assert_eq!(response["result"]["structuredContent"]["found"], true);
    assert_eq!(response["result"]["content"][0]["type"], "text");
}

#[test]
fn mcp_reports_invalid_params_for_bad_tool_call() {
    let response = mcp_call("tools/call", serde_json::json!({}));
    assert_eq!(response["error"]["code"], -32602);
    assert!(response["error"]["message"]
        .as_str()
        .unwrap()
        .contains("missing tool name"));
}

fn mcp_call(method: &str, params: serde_json::Value) -> serde_json::Value {
    let mut child = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .arg("mcp")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    let request = serde_json::json!({"id": 7, "method": method, "params": params});
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(request.to_string().as_bytes())
        .unwrap();
    let out = child.wait_with_output().unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    serde_json::from_slice(&out.stdout).unwrap()
}

#[test]
fn mcp_supports_core_parity_methods() {
    let lookup = mcp_call(
        "api_lookup",
        serde_json::json!({"symbol":"draw_text","language":"enma"}),
    );
    assert_eq!(lookup["result"]["found"], true);

    let code = mcp_call(
        "validate_code",
        serde_json::json!({"code":"int64 main(){draw_esp();return 1;}","language":"enma"}),
    );
    assert_eq!(code["result"]["ok"], false);
    assert_eq!(code["result"]["findings"][0]["kind"], "unsupported_symbol");

    let answer = mcp_call(
        "validate_answer",
        serde_json::json!({"markdown":"```enma\nint64 main(){draw_esp();return 1;}\n```"}),
    );
    assert_eq!(answer["result"]["ok"], false);
    assert_eq!(answer["result"]["blocks_checked"], 1);

    let dir = std::env::temp_dir().join("pcx_mcp_validate_project");
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("main.em"), "int64 main(){return 1;}\n").unwrap();
    let project = mcp_call(
        "validate_project",
        serde_json::json!({"path":dir.to_str().unwrap()}),
    );
    assert_eq!(project["result"]["ok"], true);
    let _ = fs::remove_dir_all(&dir);
}

#[test]
fn mcp_can_scaffold_project() {
    let dir = std::env::temp_dir().join("pcx_mcp_scaffold_project");
    let _ = fs::remove_dir_all(&dir);
    let result = mcp_call(
        "scaffold_project",
        serde_json::json!({
            "name":"MCP Demo",
            "language":"enma",
            "kind":"hello",
            "output":dir.to_str().unwrap()
        }),
    );
    assert_eq!(result["result"]["ok"], true);
    assert!(dir.join("pcx-project.json").exists());
    let _ = fs::remove_dir_all(&dir);
}

#[test]
fn native_verify_project_accepts_checked_scenarios() {
    let scenarios =
        std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../examples/scenarios");
    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args([
            "verify-project",
            scenarios.to_str().unwrap(),
            "--allow-placeholders",
            "--allow-unverified",
        ])
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
}
#[test]
fn native_create_check_answer_and_check_drift_work() {
    let dir = std::env::temp_dir().join("pcx_native_create_project");
    let _ = fs::remove_dir_all(&dir);
    let create = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args([
            "create",
            "--name",
            "Native Demo",
            "--language",
            "enma",
            "--kind",
            "hello",
            "--output",
            dir.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        create.status.success(),
        "{}",
        String::from_utf8_lossy(&create.stderr)
    );
    assert!(dir.join("pcx-project.json").exists());

    let answer = dir.join("answer.md");
    fs::write(&answer, "```enma\nint64 main(){return 1;}\n```\n").unwrap();
    let checked = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["check-answer", answer.to_str().unwrap(), "--json"])
        .output()
        .unwrap();
    assert!(
        checked.status.success(),
        "{}",
        String::from_utf8_lossy(&checked.stderr)
    );
    let json: serde_json::Value = serde_json::from_slice(&checked.stdout).unwrap();
    assert_eq!(json["ok"], true);

    let drift = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["check-drift", "--json", "--limit", "1"])
        .output()
        .unwrap();
    assert!(
        drift.status.success(),
        "{}",
        String::from_utf8_lossy(&drift.stderr)
    );
    let json: serde_json::Value = serde_json::from_slice(&drift.stdout).unwrap();
    assert_eq!(json["mode"], "offline");
    let _ = fs::remove_dir_all(&dir);
}

#[test]
fn native_check_drift_json_lists_offline_snapshot() {
    let out = Command::new(env!("CARGO_BIN_EXE_pcx-rs"))
        .args(["check-drift", "--json", "--limit", "1"])
        .env("PATH", "")
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}{}",
        String::from_utf8_lossy(&out.stderr),
        String::from_utf8_lossy(&out.stdout)
    );
    let json: serde_json::Value = serde_json::from_slice(&out.stdout).unwrap();
    assert_eq!(json["mode"], "offline");
    assert_eq!(json["snapshot"], "docs/PROVENANCE.json");
    assert_eq!(json["checked"], 1);
    assert!(json["results"].as_array().unwrap().len() <= 1);
}
