#!/usr/bin/env python3
"""pcx — The command-line manager for the pcx-ai-toolkit.

Exposes subcommands for setup, auto-updating, linting, counts generation,
drift/compatibility verification, health checks, and project scaffolding.

Usage:
    pcx setup          # compile LSP, sync skills, add to PATH
    pcx update         # self-update, rebuild LSP, sync skills, check bundles
    pcx lint [file]    # lint Enma (.em) script against the 12 guidelines
    pcx check-drift    # check documentation drift against live upstream
    pcx check-mcp      # verify MCP config is 100% in sync with mcp-api.md
    pcx check-matrix   # advisory version-matrix vs changelogs sync check
    pcx counts         # regenerate docs/COUNTS.json
    pcx version        # print the toolkit version
    pcx doctor         # health-check: verify all toolkit components are functional
    pcx new <template> [output_dir]  # scaffold a new project from a template
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "VERSION"

# ANSI colors (disabled on Windows if not supported)
def _supports_color() -> bool:
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

_COLOR = _supports_color()
_GREEN  = "\033[92m" if _COLOR else ""
_RED    = "\033[91m" if _COLOR else ""
_YELLOW = "\033[93m" if _COLOR else ""
_RESET  = "\033[0m"  if _COLOR else ""


def get_version() -> str:
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "unknown"


def run_script(script_name: str, args: list[str]) -> int:
    """Run a shell script (.sh) or PowerShell script (.ps1) based on OS."""
    is_windows = os.name == "nt"
    ext = "ps1" if is_windows else "sh"
    script_path = REPO_ROOT / f"{script_name}.{ext}"

    if not script_path.exists():
        # Try finding in tools/ subdirectory if not in root
        script_path = REPO_ROOT / "tools" / f"{script_name}.{ext}"
        if not script_path.exists():
            print(f"Error: Script {script_name}.{ext} not found.", file=sys.stderr)
            return 2

    if is_windows:
        cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)] + args
    else:
        cmd = ["bash", str(script_path)] + args

    try:
        res = subprocess.run(cmd)
        return res.returncode
    except Exception as e:
        print(f"Error executing {script_path.name}: {e}", file=sys.stderr)
        return 3


def run_python_tool(tool_name: str, args: list[str]) -> int:
    """Run a python tool in the tools/ subdirectory using the current interpreter."""
    tool_path = REPO_ROOT / "tools" / f"{tool_name}.py"
    if not tool_path.exists():
        print(f"Error: Python tool {tool_name}.py not found.", file=sys.stderr)
        return 2

    cmd = [sys.executable, str(tool_path)] + args
    try:
        res = subprocess.run(cmd)
        return res.returncode
    except Exception as e:
        print(f"Error executing {tool_name}.py: {e}\n", file=sys.stderr)
        return 3


def cmd_doctor() -> int:
    """Run a health check across all toolkit components.

    Checks: git, node, python version, LSP build artifacts, skills sync,
    docs index, and MCP server presence. Prints [OK] / [FAIL] per check.
    """
    checks: list[tuple[str, bool, str]] = []  # (label, passed, hint)

    def _run(cmd: list[str]) -> bool:
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=5)
            return r.returncode == 0
        except Exception:
            return False

    # --- Dependency checks ---
    checks.append(("git installed", _run(["git", "--version"]),
                   "Install git from https://git-scm.com/"))

    node_ok = False
    node_version = "not found"
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            node_version = r.stdout.strip()
            major = int(node_version.lstrip("v").split(".")[0])
            node_ok = major >= 18
    except Exception:
        pass
    checks.append((f"node.js >= 18 ({node_version})", node_ok,
                   "Install Node.js 18+ from https://nodejs.org/"))

    py_ok = sys.version_info >= (3, 10)
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    checks.append((f"python >= 3.10 ({py_ver})", py_ok,
                   "Upgrade Python to 3.10+ from https://python.org/"))

    # --- LSP build artifacts ---
    enma_lsp = REPO_ROOT / "lsp" / "enma-lsp" / "server" / "dist" / "server.js"
    checks.append(("enma-lsp built (server.js exists)", enma_lsp.exists(),
                   "Run: pcx setup  (or: cd lsp/enma-lsp && npm install && npm run compile)"))

    angel_lsp = REPO_ROOT / "lsp" / "angel-lsp-pcx" / "server" / "out" / "server.js"
    checks.append(("angel-lsp-pcx built (server.js exists)", angel_lsp.exists(),
                   "Run: pcx setup  (or: cd lsp/angel-lsp-pcx && npm install && npm run compile)"))

    # --- AI Skills sync ---
    local_skills = REPO_ROOT / ".claude" / "skills"
    installed_skills = Path.home() / ".claude" / "skills"
    all_skills_synced = installed_skills.is_dir()
    if all_skills_synced and local_skills.is_dir():
        missing = [d.name for d in local_skills.iterdir() if d.is_dir()
                   and not (installed_skills / d.name / "SKILL.md").exists()]
        if missing:
            all_skills_synced = False
    checks.append(("AI skills synced to ~/.claude/skills/", all_skills_synced,
                   "Run: pcx setup  to sync skills to ~/.claude/skills/"))

    # --- pcx CLI on PATH ---
    pcx_on_path = bool(shutil.which("pcx"))
    checks.append(("pcx CLI on PATH", pcx_on_path,
                   "Run: pcx setup  (or add tools/ directory to your PATH manually)"))

    # --- Docs index ---
    counts_json = REPO_ROOT / "docs" / "COUNTS.json"
    checks.append(("docs/COUNTS.json exists", counts_json.exists(),
                   "Run: pcx counts  to regenerate docs/COUNTS.json"))

    # --- MCP server ---
    mcp_dir = REPO_ROOT / "mcp" / "pcx-knowledge-mcp"
    checks.append(("mcp/pcx-knowledge-mcp/ present", mcp_dir.is_dir(),
                   "Re-clone with: git clone --recursive ..."))

    # --- Print results ---
    print(f"\npcx-ai-toolkit v{get_version()} - Doctor Report\n" + "-" * 50)
    passed = 0
    failed_checks: list[tuple[str, str]] = []
    for label, ok, hint in checks:
        tag = f"{_GREEN}[OK]  {_RESET}" if ok else f"{_RED}[FAIL]{_RESET}"
        print(f"  {tag} {label}")
        if ok:
            passed += 1
        else:
            failed_checks.append((label, hint))

    print("-" * 50)
    total = len(checks)
    if not failed_checks:
        print(f"{_GREEN}All {total} checks passed.{_RESET}\n")
        return 0
    else:
        print(f"{_RED}{len(failed_checks)}/{total} checks failed.{_RESET}\n")
        print("Suggested fixes:")
        for label, hint in failed_checks:
            print(f"  - {label}")
            print(f"    -> {_YELLOW}{hint}{_RESET}")
        print()
        return 1


def cmd_new(args: list[str]) -> int:
    """Scaffold a new PCX project from a template.

    Usage:
        pcx new <template>              # scaffold into current directory
        pcx new <template> <output>     # scaffold into <output> directory
    """
    templates_dir = REPO_ROOT / "templates"

    def list_templates() -> None:
        print("Available templates:")
        for item in sorted(templates_dir.iterdir()):
            if item.is_dir():
                readme = item / "README.md"
                desc = ""
                if readme.exists():
                    first_line = readme.read_text(encoding="utf-8", errors="ignore").splitlines()
                    desc = " — " + first_line[0].lstrip("#").strip() if first_line else ""
                print(f"  {item.name}{desc}")
            elif item.suffix == ".em":
                print(f"  {item.stem}  ({item.name})")

    if not args or any(a in ("-h", "--help") for a in args):
        print("Usage: pcx new <template> [output_dir]\n")
        list_templates()
        return 0 if any(a in ("-h", "--help") for a in args) else 1

    template_name = args[0]
    output_dir = Path(args[1]) if len(args) > 1 else Path.cwd() / template_name

    # Try directory template first
    template_path = templates_dir / template_name
    if template_path.is_dir():
        if output_dir.exists():
            print(f"Error: Output directory '{output_dir}' already exists.", file=sys.stderr)
            return 1
        shutil.copytree(str(template_path), str(output_dir))
        files = list(output_dir.rglob("*"))
        print(f"{_GREEN}Created project from template '{template_name}':{_RESET}")
        for f in sorted(files):
            if f.is_file():
                print(f"  {f.relative_to(output_dir)}")
        print(f"\nProject directory: {output_dir}")
        print("Next: open in your editor and run pcx lint <main.em> to validate.")
        return 0

    # Try single-file template (.em)
    template_file = templates_dir / f"{template_name}.em"
    if template_file.exists():
        out_file = output_dir if str(output_dir).endswith(".em") else output_dir / f"{template_name}.em"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(template_file), str(out_file))
        print(f"{_GREEN}Created {out_file} from template '{template_name}'{_RESET}")
        return 0

    print(f"Error: Template '{template_name}' not found.\n", file=sys.stderr)
    list_templates()
    return 1


def main() -> int:
    desc = f"pcx-ai-toolkit manager CLI v{get_version()}"
    ap = argparse.ArgumentParser(description=desc, usage="pcx <command> [args]")
    ap.add_argument("-V", "--version", action="version",
                    version=f"pcx-ai-toolkit v{get_version()}")
    ap.add_argument("command", nargs="?", help=(
        "Command to run: setup, update, lint, check-drift, check-mcp, "
        "check-matrix, counts, version, doctor, new, help"
    ))
    ap.add_argument("args", nargs=argparse.REMAINDER, help="Subcommand arguments")
    args = ap.parse_args()

    if args.command is None:
        ap.print_help()
        return 0

    cmd = args.command.lower()
    sub_args = args.args

    if cmd in ("version", "-v", "--version"):
        print(f"pcx-ai-toolkit v{get_version()}")
        return 0

    if cmd == "help":
        ap.print_help()
        return 0

    if cmd == "setup":
        return run_script("setup", sub_args)

    if cmd == "update":
        return run_script("update-toolkit", sub_args)

    if cmd == "lint":
        return run_python_tool("script-linter", sub_args)

    if cmd == "check-drift":
        return run_python_tool("check-doc-drift", sub_args)

    if cmd == "check-mcp":
        return run_python_tool("check-mcp-config", sub_args)

    if cmd == "check-matrix":
        return run_python_tool("check-version-matrix", sub_args)

    if cmd == "counts":
        return run_python_tool("build-counts", sub_args)

    if cmd == "doctor":
        return cmd_doctor()

    if cmd == "new":
        return cmd_new(sub_args)

    print(f"Error: Unknown command '{cmd}'. Run 'pcx --help' or check usage.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())