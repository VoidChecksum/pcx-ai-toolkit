import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("auto_release", ROOT / "tools" / "auto-release.py")
auto_release = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(auto_release)


def test_bump_kind_uses_conventional_commits():
    assert auto_release.bump_kind(["docs: update readme"]) is None
    assert auto_release.bump_kind(["fix(cli): handle empty input"]) == "patch"
    assert auto_release.bump_kind(["fix(cli): handle empty input", "feat(mcp): add planner"]) == "minor"
    assert auto_release.bump_kind(["feat(api)!: remove old endpoint"]) == "major"
    assert auto_release.bump_kind(["feat(api): remove old endpoint\n\nBREAKING CHANGE: old endpoint removed"]) == "major"


def test_bump_semver():
    assert auto_release.bump((1, 2, 3), "patch") == (1, 2, 4)
    assert auto_release.bump((1, 2, 3), "minor") == (1, 3, 0)
    assert auto_release.bump((1, 2, 3), "major") == (2, 0, 0)
