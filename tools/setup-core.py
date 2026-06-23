#!/usr/bin/env python3
"""Shared core setup logic for pcx-ai-toolkit.

This script builds LSP servers, compiles the Rust native tools, installs Claude Code
skills, and optionally copies project rules. It is designed to be invoked by both
setup.sh and setup.ps1 thin wrappers.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUST_TOOLS = ("pe-parser", "sig-uniqueness-checker", "binary-diff-summary", "offset-diff")


class CmdResult:
    def __init__(self, ok: bool, stdout: str = "", stderr: str = "") -> None:
        self.ok = ok
        self.stdout = stdout
        self.stderr = stderr


def run_command(cmd: list[str], cwd: Path) -> CmdResult:
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
        return CmdResult(res.returncode == 0, res.stdout or "", res.stderr or "")
    except subprocess.TimeoutExpired as e:
        return CmdResult(False, stderr=f"timed out after {e.timeout}s")
    except Exception as e:
        return CmdResult(False, stderr=str(e))


def _print_failure(cmd: list[str], res: CmdResult) -> None:
    print(f"    command: {' '.join(cmd)}")
    if res.stdout.strip():
        print("    stdout:")
        for line in res.stdout.strip().splitlines():
            print(f"      {line}")
    if res.stderr.strip():
        print("    stderr:")
        for line in res.stderr.strip().splitlines():
            print(f"      {line}")


def build_lsp(name: str, path: Path, out_file: str) -> None:
    print(f"[..] Building {name}...")
    if not (path / "package.json").exists():
        print(f"[!!] {name} directory not found or invalid. Run: git submodule update --init --recursive")
        return

    if not shutil.which("npm"):
        print("[!!] npm not found. Skipping LSP build. Install Node.js 18+ first.")
        return

    install = run_command(["npm", "install"], path)
    if not install.ok:
        print(f"[!!] {name}: npm install failed")
        _print_failure(["npm", "install"], install)
        return

    compile_ = run_command(["npm", "run", "compile"], path)
    if not compile_.ok:
        print(f"[!!] {name}: npm run compile failed")
        _print_failure(["npm", "run", "compile"], compile_)
        return

    if (path / out_file).exists():
        print(f"[ok] {name} built successfully: {out_file}")
    else:
        print(f"[!!] {name} build did not produce {out_file}")


def build_rust_tools() -> None:
    parser_dir = REPO_ROOT / "tools" / "pe-parser"
    bin_dir = REPO_ROOT / "tools" / "bin"

    if not parser_dir.exists():
        return

    if not shutil.which("cargo"):
        print("\n[--] Cargo not found — using Python implementations of binary tools")
        return

    print("\n[..] Building Rust native tools...")
    build = run_command(["cargo", "build", "--release"], parser_dir)
    if not build.ok:
        print("[!!] Rust native tool build failed — falling back to Python implementations")
        _print_failure(["cargo", "build", "--release"], build)
        return

    bin_dir.mkdir(parents=True, exist_ok=True)
    ext = ".exe" if os.name == "nt" else ""
    copied: list[str] = []
    for tool in RUST_TOOLS:
        src_bin = parser_dir / "target" / "release" / f"{tool}{ext}"
        dest_bin = bin_dir / f"{tool}{ext}"
        if not src_bin.exists():
            print(f"[!!] Rust build did not produce {src_bin.name}")
            continue
        try:
            shutil.copy2(src_bin, dest_bin)
            copied.append(f"tools/bin/{tool}{ext}")
        except Exception as e:
            print(f"[!!] Failed to copy Rust binary {src_bin.name}: {e}")
    if copied:
        print(f"[ok] Rust native tools built: {', '.join(copied)}")


def sync_skills() -> None:
    home_dir = Path.home()
    claude_skills = home_dir / ".claude" / "skills"
    local_skills = REPO_ROOT / ".claude" / "skills"

    if not local_skills.exists():
        print("[!!] Local skills directory not found.")
        return

    if not (home_dir / ".claude").is_dir():
        print("\n[--] Claude Code not detected — skip skill install.")
        print(f"     Manual: copy {local_skills.relative_to(REPO_ROOT)} to ~/.claude/skills/")
        return

    print("\n[..] Claude Code detected — installing skills...")
    installed = 0
    try:
        for skill_dir in local_skills.iterdir():
            if not skill_dir.is_dir():
                continue
            dest_dir = claude_skills / skill_dir.name
            dest_dir.mkdir(parents=True, exist_ok=True)
            copied = 0
            for md_file in skill_dir.glob("*.md"):
                shutil.copy2(md_file, dest_dir / md_file.name)
                copied += 1
            if copied:
                installed += 1
        print(f"[ok] {installed} skills installed to {claude_skills}")
    except Exception as e:
        print(f"[!!] Failed to sync skills: {e}")


def copy_rules(project_path: str) -> None:
    p_path = Path(project_path).resolve()
    if not p_path.is_dir():
        print(f"[!!] Project path not found: {project_path}")
        return

    src_rules = REPO_ROOT / "rules" / "CLAUDE.md"
    if src_rules.exists():
        try:
            shutil.copy2(src_rules, p_path / "CLAUDE.md")
            print(f"[ok] Project rules copied to {p_path}/CLAUDE.md")
        except Exception as e:
            print(f"[!!] Failed to copy rules: {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Core setup utility for pcx-ai-toolkit.")
    ap.add_argument("--project", help="Copy rules/CLAUDE.md to the specified project directory")
    args = ap.parse_args()

    # 1. Update submodules
    print("[..] Checking git submodules...")
    run_command(["git", "submodule", "update", "--init", "--recursive"], REPO_ROOT)

    # 2. Build LSP servers
    build_lsp("enma-lsp", REPO_ROOT / "lsp" / "enma-lsp", "server/dist/server.js")
    build_lsp("angel-lsp-pcx", REPO_ROOT / "lsp" / "angel-lsp-pcx", "server/out/server.js")

    # 3. Build Rust native tools
    build_rust_tools()

    # 4. Sync Claude Code skills
    sync_skills()

    # 5. Copy project rules if requested
    if args.project:
        copy_rules(args.project)

    # 6. Ensure the CLI wrapper is executable on Unix
    pcx_wrapper = REPO_ROOT / "tools" / "pcx"
    if pcx_wrapper.exists() and os.name != "nt":
        try:
            pcx_wrapper.chmod(0o755)
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
