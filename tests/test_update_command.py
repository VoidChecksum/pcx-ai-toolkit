import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class UpdateCommandTest(unittest.TestCase):
    def _make_repo(self, script_name: str, *, dirty: bool = False, tracked_dirty: bool = False) -> Path:
        temp = Path(tempfile.mkdtemp())
        remote = temp / "remote.git"
        repo = temp / "repo"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
        (repo / "tools").mkdir()
        shutil.copy(REPO_ROOT / "tools" / script_name, repo / "tools" / script_name)
        (repo / "VERSION").write_text("0.0.0\n", encoding="utf-8")
        (repo / "tracked.txt").write_text("clean\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(remote)], check=True)
        subprocess.run(["git", "-C", str(repo), "push", "-u", "origin", "main"], check=True, capture_output=True)
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
            shutil.rmtree(repo.parent)

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
                shutil.rmtree(repo.parent)

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
            shutil.rmtree(repo.parent)

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
                shutil.rmtree(repo.parent)


if __name__ == "__main__":
    unittest.main()
