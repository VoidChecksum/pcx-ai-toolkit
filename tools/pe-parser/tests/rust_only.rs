use std::{
    fs,
    path::{Path, PathBuf},
};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn collect_files(dir: &Path, out: &mut Vec<PathBuf>) {
    let name = dir.file_name().and_then(|n| n.to_str()).unwrap_or("");
    if matches!(
        name,
        ".git" | "target" | "node_modules" | "dist" | "packages"
    ) {
        return;
    }
    for entry in fs::read_dir(dir).unwrap() {
        let path = entry.unwrap().path();
        if path.is_dir() {
            collect_files(&path, out);
        } else {
            out.push(path);
        }
    }
}

fn repo_files() -> Vec<PathBuf> {
    let mut files = Vec::new();
    collect_files(&repo_root(), &mut files);
    files
}

fn rel(path: &Path) -> String {
    path.strip_prefix(repo_root())
        .unwrap()
        .display()
        .to_string()
}

#[test]
fn repository_has_no_project_owned_python_files() {
    let offenders: Vec<String> = repo_files()
        .into_iter()
        .filter(|path| {
            path.extension().and_then(|e| e.to_str()) == Some("py")
                || path.file_name().and_then(|n| n.to_str()) == Some("pyproject.toml")
        })
        .map(|path| rel(&path))
        .collect();

    assert!(offenders.is_empty(), "Python files remain: {offenders:#?}");
}

#[test]
fn ci_and_release_do_not_install_or_publish_python() {
    let checked = [
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        ".github/workflows/doc-drift.yml",
        ".github/workflows/publish-mcp.yml",
        "package.json",
        "npm/bin/pcx.js",
    ];
    let forbidden = [
        "setup-python",
        "python3",
        "python ",
        "pip",
        "PyPI",
        "pypi",
        ".py",
    ];
    let mut hits = Vec::new();

    for rel_path in checked {
        let path = repo_root().join(rel_path);
        if !path.exists() {
            continue;
        }
        let text = fs::read_to_string(&path).unwrap();
        for needle in forbidden {
            if text.contains(needle) {
                hits.push(format!("{rel_path}: {needle}"));
            }
        }
    }

    assert!(
        hits.is_empty(),
        "Python packaging/CI references remain: {hits:#?}"
    );
}

#[test]
fn pcx_rs_has_no_python_fallback() {
    let text = fs::read_to_string(repo_root().join("tools/pe-parser/src/bin/pcx-rs.rs")).unwrap();
    for needle in [
        "python_cmd",
        "run_python_fallback",
        "Compatibility commands delegated to Python",
    ] {
        assert!(!text.contains(needle), "pcx-rs still contains {needle}");
    }
}
