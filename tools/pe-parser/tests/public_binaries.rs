use std::path::Path;

const PUBLIC_BINARIES: &[(&str, &str)] = &[
    ("pe-parser", env!("CARGO_BIN_EXE_pe-parser")),
    ("pcx-rs", env!("CARGO_BIN_EXE_pcx-rs")),
    ("api-lookup", env!("CARGO_BIN_EXE_api-lookup")),
    (
        "pattern-format-converter",
        env!("CARGO_BIN_EXE_pattern-format-converter"),
    ),
    (
        "sig-uniqueness-checker",
        env!("CARGO_BIN_EXE_sig-uniqueness-checker"),
    ),
    (
        "binary-diff-summary",
        env!("CARGO_BIN_EXE_binary-diff-summary"),
    ),
    ("offset-diff", env!("CARGO_BIN_EXE_offset-diff")),
    (
        "anti-debug-scanner",
        env!("CARGO_BIN_EXE_anti-debug-scanner"),
    ),
    (
        "identify-protector",
        env!("CARGO_BIN_EXE_identify-protector"),
    ),
    (
        "pe-section-analyzer",
        env!("CARGO_BIN_EXE_pe-section-analyzer"),
    ),
    ("analyze-vmprotect", env!("CARGO_BIN_EXE_analyze-vmprotect")),
    ("dump-strings-xor", env!("CARGO_BIN_EXE_dump-strings-xor")),
    (
        "module-export-mapper",
        env!("CARGO_BIN_EXE_module-export-mapper"),
    ),
];

#[test]
fn public_binary_names_are_preserved() {
    for (expected_name, binary_path) in PUBLIC_BINARIES {
        let file_name = Path::new(binary_path)
            .file_name()
            .and_then(|name| name.to_str());

        assert_eq!(Some(*expected_name), file_name);
    }
}
