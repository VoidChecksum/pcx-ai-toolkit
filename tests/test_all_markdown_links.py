import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {'.git', '.venv', 'node_modules', 'target', 'dist', 'build'}
PATH_RE = re.compile(r'(?:\]\(([^)]+)\)|`([^`]+\.(?:md|json)(?:#[^`]+)?)`)')


def markdown_files():
    for path in (REPO_ROOT / 'docs').rglob('*.md'):
        if any(part in SKIP_DIRS for part in path.parts) or path.name.startswith('llms'):
            continue
        yield path


def anchors(text: str) -> set[str]:
    out = set()
    for line in text.splitlines():
        if line.startswith('#'):
            title = line.lstrip('#').strip().lower()
            slug = re.sub(r'[^a-z0-9\s-]', '', title)
            slug = re.sub(r'\s+', '-', slug).strip('-')
            if slug:
                out.add(slug)
    return out


class AllMarkdownLinksTest(unittest.TestCase):
    def test_relative_markdown_and_json_links_exist(self):
        for doc in markdown_files():
            text = doc.read_text(encoding='utf-8', errors='ignore')
            for m in PATH_RE.finditer(text):
                raw = (m.group(1) or m.group(2) or '').strip()
                if not raw or raw.startswith(('http://', 'https://', 'mailto:', '#')):
                    continue
                raw = raw.split()[0]
                target, _, anchor = raw.partition('#')
                if target.startswith(('/', '~', 'extensions/')) or '*' in target or '$' in target or '<' in target or target.startswith('pcx '):
                    continue
                if not target.endswith(('.md', '.json')):
                    continue
                if not (target.startswith(('.', 'docs/', 'knowledge/', 'schemas/', 'evals/', 'mcp/', 'tests/', '.claude/', 'labs/')) or '/' in target):
                    continue
                path = (REPO_ROOT / target).resolve() if target.startswith(('docs/', 'knowledge/', 'schemas/', 'evals/', 'mcp/', 'tests/', '.claude/', 'labs/')) else (doc.parent / target).resolve()
                with self.subTest(doc=doc.relative_to(REPO_ROOT), link=raw):
                    self.assertTrue(path.exists(), f'{raw} -> {path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}')
                    if anchor and path.suffix == '.md':
                        self.assertIn(anchor.lower(), anchors(path.read_text(encoding='utf-8', errors='ignore')))

if __name__ == '__main__':
    unittest.main()
