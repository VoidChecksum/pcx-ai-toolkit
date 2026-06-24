use pe_parser::validators::{symbol_check, verify_project};
use std::{fs, path::PathBuf};
fn root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}
#[test]
fn rejects_bad() {
    let p = std::env::temp_dir().join("pcx_bad.em");
    fs::write(
        &p,
        "int64 main(){draw_esp();return 1;}
",
    )
    .unwrap();
    let f = symbol_check(&root(), &p).unwrap();
    assert!(f.iter().any(|x| x.symbol == "draw_esp"));
    let _ = fs::remove_file(p);
}
#[test]
fn rejects_wrong_lang() {
    let p = std::env::temp_dir().join("pcx_bad.as");
    fs::write(
        &p,
        "int main(){register_routine(0,0);return 1;}
",
    )
    .unwrap();
    let f = symbol_check(&root(), &p).unwrap();
    assert!(f.iter().any(|x| x.symbol == "register_routine"));
    let _ = fs::remove_file(p);
}

#[test]
fn rejects_lua_denylist_symbol() {
    let p = std::env::temp_dir().join("pcx_lua_bad.em");
    fs::write(&p, "int64 main(){lua_pcall();return 1;}\n").unwrap();
    let f = symbol_check(&root(), &p).unwrap();
    assert!(f
        .iter()
        .any(|x| x.kind == "unsupported_symbol" && x.symbol == "lua_pcall"));
    let _ = fs::remove_file(p);
}

#[test]
fn rejects_json_denylist_symbol() {
    let p = std::env::temp_dir().join("pcx_json_denylist_bad.em");
    fs::write(&p, "int64 main(){read_view_angles();return 1;}\n").unwrap();
    let f = symbol_check(&root(), &p).unwrap();
    assert!(f.iter().any(|x| x.kind == "unsupported_symbol"
        && x.symbol == "read_view_angles"
        && x.message.contains("Perception API index")));
    let _ = fs::remove_file(p);
}

#[test]
fn reports_missing_enma_import() {
    let p = std::env::temp_dir().join("pcx_missing_import.em");
    fs::write(
        &p,
        "int64 main(){color c = color(255,255,255,255);return 1;}\n",
    )
    .unwrap();
    let f = symbol_check(&root(), &p).unwrap();
    assert!(f
        .iter()
        .any(|x| x.kind == "missing_import" && x.symbol == "color"));
    let _ = fs::remove_file(p);
}

#[test]
fn rejects_enma_map_int_keys() {
    let p = std::env::temp_dir().join("pcx_map_key_bad.em");
    fs::write(
        &p,
        "import \"maps\"\nint64 main(){map<int64, int64> counts; return 1;}\n",
    )
    .unwrap();
    let f = symbol_check(&root(), &p).unwrap();
    assert!(f
        .iter()
        .any(|x| x.kind == "semantic_error" && x.symbol == "map<int64"));
    let _ = fs::remove_file(p);
}

#[test]
fn rejects_returning_address_of_local() {
    let p = std::env::temp_dir().join("pcx_pointer_escape_bad.em");
    fs::write(&p, "int64* leak(){int64 local = 1; return &local;}\n").unwrap();
    let f = symbol_check(&root(), &p).unwrap();
    assert!(f
        .iter()
        .any(|x| x.kind == "semantic_error" && x.symbol == "return &"));
    let _ = fs::remove_file(p);
}

#[test]
fn reports_missing_file_permission() {
    let p = std::env::temp_dir().join("pcx_file_permission_bad.em");
    fs::write(
        &p,
        "import \"file\"\nint64 main(){string x = fs_read_file(\"x.txt\"); return 1;}\n",
    )
    .unwrap();
    let f = symbol_check(&root(), &p).unwrap();
    assert!(f
        .iter()
        .any(|x| x.kind == "missing_permission" && x.symbol == "PERM_FILE"));
    let _ = fs::remove_file(p);
}
#[test]
fn verify_empty() {
    let d = std::env::temp_dir().join("pcx_empty");
    let _ = fs::create_dir_all(&d);
    assert!(verify_project(&root(), &d, false, false)
        .unwrap_err()
        .contains("no .em"));
    let _ = fs::remove_dir_all(d);
}
