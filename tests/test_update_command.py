import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _remove_tree(path: Path) -> None:
    def make_writable_and_retry(func, failing_path, _exc):
        os.chmod(failing_path, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        func(failing_path)

    for attempt in range(3):
        try:
            if sys.version_info >= (3, 12):
                shutil.rmtree(path, onexc=make_writable_and_retry)
            else:
                shutil.rmtree(path, onerror=make_writable_and_retry)
            return
        except PermissionError:
            if attempt == 2:
                raise
            time.sleep(0.1)


def _bash_path(path: Path) -> str | None:
    if os.name != "nt" or not shutil.which("bash"):
        return None
    result = subprocess.run(["bash", "-lc", "pwd"], cwd=path, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


class UpdateCommandTest(unittest.TestCase):
    def _make_repo(self, script_name: str, *, dirty: bool = False, tracked_dirty: bool = False) -> Path:
        temp = Path(tempfile.mkdtemp())
        remote = temp / "remote.git"
        repo = temp / "repo"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "core.autocrlf", "false"], check=True)
        (repo / "tools").mkdir()
        shutil.copy(REPO_ROOT / "tools" / script_name, repo / "tools" / script_name)
        (repo / "VERSION").write_text("0.0.0\n", encoding="utf-8")
        (repo / "tracked.txt").write_text("clean\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(remote)], check=True)
        subprocess.run(["git", "-C", str(repo), "push", "-u", "origin", "main"], check=True, capture_output=True)
        if os.name == "nt" and script_name.endswith(".sh"):
            bash_remote = _bash_path(remote)
            if bash_remote:
                subprocess.run(["git", "-C", str(repo), "remote", "set-url", "origin", bash_remote], check=True)
        if tracked_dirty:
            (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
        elif dirty:
            (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        return repo

    def test_bash_update_accepts_clean_forced_run(self):
        repo = self._make_repo("update-toolkit.sh")
        try:
            result = subprocess.run(
                ["bash", "tools/update-toolkit.sh", "--force", "--skip-lsp", "--skip-skills", "--skip-bundles"],
                cwd=repo,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Update complete.", result.stdout)
        finally:
            _remove_tree(repo.parent)

    def test_bash_update_rejects_uncommitted_changes(self):
        for tracked_dirty in (False, True):
            repo = self._make_repo("update-toolkit.sh", dirty=not tracked_dirty, tracked_dirty=tracked_dirty)
            try:
                result = subprocess.run(
                    ["bash", "tools/update-toolkit.sh", "--force", "--skip-lsp", "--skip-skills", "--skip-bundles"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertIn("Uncommitted changes detected", result.stderr)
            finally:
                _remove_tree(repo.parent)

    @unittest.skipIf(os.name == "nt", "sh stub is POSIX-only")
    def test_python_cli_delegates_update_to_rust_when_available(self):
        repo = self._make_repo("update-toolkit.sh")
        try:
            shutil.copy(REPO_ROOT / "tools" / "pcx.py", repo / "tools" / "pcx.py")
            shutil.copytree(REPO_ROOT / "tools" / "lib", repo / "tools" / "lib")
            bin_dir = repo / "tools" / "bin"
            bin_dir.mkdir()
            rust = bin_dir / ("pcx-rs.exe" if os.name == "nt" else "pcx-rs")
            rust.write_text("#!/usr/bin/env sh\nprintf '%s\n' \"$@\"\n", encoding="utf-8")
            rust.chmod(0o755)

            result = subprocess.run(
                [sys.executable, "tools/pcx.py", "update", "--plan-json"],
                cwd=repo,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("update", result.stdout)
            self.assertIn("--plan-json", result.stdout)
        finally:
            _remove_tree(repo.parent)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell not installed")
    def test_powershell_update_accepts_clean_forced_run(self):
        repo = self._make_repo("update-toolkit.ps1")
        try:
            result = subprocess.run(
                ["pwsh", "-NoLogo", "-NoProfile", "-File", "tools/update-toolkit.ps1", "-Force", "-SkipLsp", "-SkipSkills", "-SkipBundles"],
                cwd=repo,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Update complete.", result.stdout)
        finally:
            _remove_tree(repo.parent)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell not installed")
    def test_powershell_update_rejects_uncommitted_changes(self):
        for tracked_dirty in (False, True):
            repo = self._make_repo("update-toolkit.ps1", dirty=not tracked_dirty, tracked_dirty=tracked_dirty)
            try:
                result = subprocess.run(
                    ["pwsh", "-NoLogo", "-NoProfile", "-File", "tools/update-toolkit.ps1", "-Force", "-SkipLsp", "-SkipSkills", "-SkipBundles"],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertIn("Uncommitted changes detected", result.stdout + result.stderr)
            finally:
                _remove_tree(repo.parent)


if __name__ == "__main__":
    unittest.main()
