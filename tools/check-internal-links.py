#!/usr/bin/env python3
"""Check internal markdown links (used by CI)."""
import re
import os
import glob
import urllib.parse
import sys

link_re = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
code_fence = re.compile(r'```[\s\S]*?```', re.MULTILINE)
broken = []
for md in glob.glob('**/*.md', recursive=True):
    md = md.replace(os.sep, '/')
    if md.startswith('lsp/'): continue
    if md.startswith('docs/llms-'): continue
    d = os.path.dirname(md)
    try:
        txt = open(md, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    clean = code_fence.sub('', txt)
    for m in link_re.finditer(clean):
        tgt = m.group(1).strip()
        if tgt.startswith(('http://','https://','#','mailto:','skill://')): continue
        tgt_clean = urllib.parse.unquote(tgt.split('#')[0].strip())
        if not tgt_clean or ' ' in tgt_clean: continue
        if '/' not in tgt_clean and '.' not in tgt_clean: continue
        p = os.path.normpath(os.path.join(d, tgt_clean))
        if not os.path.exists(p):
            broken.append(f"  {md} -> {tgt_clean}")
if broken:
    print(f"Broken internal links ({len(broken)}):")
    for b in broken: print(b)
    sys.exit(1)
print("All internal links valid")
