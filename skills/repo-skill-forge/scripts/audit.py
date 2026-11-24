#!/usr/bin/env python3
"""Monthly audit for a skill made by repo-skill-forge (the "dreaming" pass).

Compares what the skill and its reference docs mention with the code as it is now:
  1. files and names the docs mention that no longer exist in the code (stale)
  2. code files that no doc mentions (missing)

  python3 audit.py --repo PATH --docs DIR [--skill SKILL.md]

It only reports. Turning the report into edits is a proposal for the owner to approve.
"""
import argparse, re, subprocess
from pathlib import Path

SKIP_PARTS = ('/node_modules/', '/vendor/', '/dist/', '/build/', '/font/', '/fonts/', '/.next/')
SKIP_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.svg', '.woff', '.woff2', '.ttf',
            '.otf', '.mp4', '.mp3', '.zip', '.gz', '.pdf', '.wasm', '.lock', '.min.js', '.min.css', '.map')
CODE_EXT = r'(?:js|mjs|cjs|ts|tsx|jsx|css|scss|html|vue|svelte|py|rb|php|go|rs|java|kt|swift|sql|sh)'
# words that appear in backticks inside skills but are commands or placeholders, not code names
GENERIC = {'grep', 'cut', 'cat', 'git', 'node', 'python3', 'npm', 'npx', 'pnpm', 'yarn', 'bash', 'curl',
           'assert', 'diff', 'access', 'push', 'main', 'PATTERN', 'FILES', 'FILE', 'REPO', 'PATH',
           'SKILL_PATH', 'old_string', 'offset', 'limit', 'edits', 'shortcut', 'true', 'false', 'null'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--docs', required=True, help='folder with the reference .md files')
    ap.add_argument('--skill', action='append', default=[], help='SKILL.md path (repeatable)')
    a = ap.parse_args()
    repo = Path(a.repo).resolve()

    docs = sorted(Path(a.docs).glob('*.md')) + [Path(p) for p in a.skill]
    text = '\n'.join(p.read_text(errors='ignore') for p in docs)
    tick = ' '.join(re.findall(r'`([^`\n]+)`', text))

    listed = subprocess.run(['git', 'ls-files'], cwd=repo, capture_output=True, text=True).stdout.split()
    code = [f for f in listed if not f.lower().endswith(SKIP_EXT)
            and not any(p in '/' + f for p in SKIP_PARTS) and not f.startswith(('docs/claude/', '.claude/'))]
    names = {f.rsplit('/', 1)[-1] for f in listed}
    src = '\n'.join((repo / f).read_text(errors='ignore') for f in code if (repo / f).is_file())

    placeholder = re.compile(r'/X\.|\bX\.|<|\*')
    gone_files = sorted({t for t in re.findall(r'[\w./-]+\.' + CODE_EXT + r'\b', tick)
                         if t.rsplit('/', 1)[-1] not in names and not placeholder.search(t)})
    # tool names, commands or placeholders can be listed in the docs: <!-- audit-ignore: name1 name2 -->
    ignore = set(' '.join(re.findall(r'audit-ignore:([^>]*)-->', text)).split())
    idents = set(re.findall(r'(?<![\w./-])([A-Za-z_][\w-]{3,})(?![\w./])', tick)) - GENERIC - ignore
    gone = sorted(w for w in idents if w not in src and not w.isupper() and not w.endswith('X'))

    globs = [g[:-1] for g in re.findall(r'[\w./-]+/\*', tick)]  # a doc naming dir/* covers its files
    missing = sorted(f for f in code if f.rsplit('/', 1)[-1] not in text and not any(g in f for g in globs)
                     and re.search(r'\.' + CODE_EXT + r'$', f))

    print('stale files (in docs, not in code):', gone_files or 'none')
    print('stale names (in docs, not in code):', gone or 'none')
    print('undocumented code files:', missing or 'none')


if __name__ == '__main__':
    main()
