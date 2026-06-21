#!/usr/bin/env python3
"""Shared core setup logic for pcx-ai-toolkit.

This script builds LSP servers, compiles the Rust pe-parser, installs Claude Code
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


def run_command(cmd: list[str], cwd: Path) -> bool:
    try:
        res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except Exception:
        return False


def build_lsp(name: str, path: Path, out_file: str) -> None:
    print(f"[..] Building {name}...")
    if not (path / "package.json").exists():
        print(f"[!!] {name} directory not found or invalid.")
        return

    # Check for npm
    if not shutil.which("npm"):
        print("[!!] npm not found. Skipping LSP build. Install Node.js first.")
        return

    # Run npm install and npm run compile
    ok = run_command(["npm", "install"], path) and run_command(["npm", "run", "compile"], path)
    if ok and (path / out_file).exists():
        print(f"[ok] {name} built successfully: {out_file}")
    else:
        print(f"[!!] {name} build failed. Run manually in {path.relative_to(REPO_ROOT)}")


def build_rust_parser() -> None:
    parser_dir = REPO_ROOT / "tools" / "pe-parser"
    bin_dir = REPO_ROOT / "tools" / "bin"

    if not parser_dir.exists():
        return

    if not shutil.which("cargo"):
        print("\n[--] Cargo not found — using Python implementations of PE parser")
        return

    print("\n[..] Building Rust core parser (pe-parser)...")
    ok = run_command(["cargo", "build", "--release"], parser_dir)
    if ok:
        bin_dir.mkdir(parents=True, exist_ok=True)
        ext = ".exe" if os.name == "nt" else ""
        src_bin = parser_dir / "target" / "release" / f"pe-parser{ext}"
        dest_bin = bin_dir / f"pe-parser{ext}"
        try:
            shutil.copy2(src_bin, dest_bin)
            print(f"[ok] Rust core parser built: tools/bin/pe-parser{ext}")
        except Exception as e:
            print(f"[!!] Failed to copy Rust binary: {e}")
    else:
        print("[!!] Rust core build failed — falling back to Python implementations")


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
    try:
        for skill_dir in local_skills.iterdir():
            if skill_dir.is_dir():
                src_skill = skill_dir / "SKILL.md"
                if src_skill.exists():
                    dest_dir = claude_skills / skill_dir.name
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_skill, dest_dir / "SKILL.md")
        print(f"[ok] Skills installed to {claude_skills}")
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

    # 3. Build Rust PE parser
    build_rust_parser()

    # 4. Sync Claude Code skills
    sync_skills()

    # 5. Copy project rules if requested
    if args.project:
        copy_rules(args.project)

    return 0


if __name__ == "__main__":
    sys.exit(main())
