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
fn verify_empty() {
    let d = std::env::temp_dir().join("pcx_empty");
    let _ = fs::create_dir_all(&d);
    assert!(verify_project(&root(), &d, false, false)
        .unwrap_err()
        .contains("no .em"));
    let _ = fs::remove_dir_all(d);
}
