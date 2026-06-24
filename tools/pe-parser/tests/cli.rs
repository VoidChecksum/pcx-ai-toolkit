use std::{
    fs,
    io::Write,
    process::{Command, Stdio},
};

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
