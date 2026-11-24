#!/usr/bin/env python3
"""Cheap repository scan for repo-skill-forge.

Prints, in a few hundred tokens, what a per-repo skill needs to know:
layout, big files, very long lines, platform hints, folders never to open,
and possible secrets (location and kind only, never the value).

  python3 scan.py REPO              full scan of a git checkout
  python3 scan.py --secrets FILE..  secret check only (run it on generated docs)
"""
import os, re, subprocess, sys
from collections import Counter

SKIP_DIRS = ('node_modules/', 'vendor/', 'dist/', 'build/', '.next/', 'out/', 'target/',
             '__pycache__/', '.venv/', 'venv/', 'coverage/', '/font/', '/fonts/')
SKIP_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.svg', '.woff', '.woff2',
            '.ttf', '.otf', '.eot', '.mp4', '.mp3', '.wav', '.zip', '.gz', '.pdf', '.wasm',
            '.lock', '.min.js', '.min.css', '.map')
LOCKS = ('package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'Cargo.lock',
         'composer.lock', 'Gemfile.lock', 'bun.lockb')

# file or folder name -> what it tells the skill about the platform
HINTS = {
    'wrangler.toml': 'Cloudflare Workers (wrangler)', 'wrangler.jsonc': 'Cloudflare Workers (wrangler)',
    'wrangler.json': 'Cloudflare Workers (wrangler)', 'vercel.json': 'Vercel', 'netlify.toml': 'Netlify',
    'firebase.json': 'Firebase', 'fly.toml': 'Fly.io', 'render.yaml': 'Render', 'app.yaml': 'Google App Engine',
    'Dockerfile': 'Docker', 'docker-compose.yml': 'Docker Compose', 'compose.yaml': 'Docker Compose',
    'package.json': 'Node.js (read its scripts)', 'deno.json': 'Deno', 'bun.lockb': 'Bun',
    'pyproject.toml': 'Python (pyproject)', 'requirements.txt': 'Python (pip)', 'manage.py': 'Django',
    'Gemfile': 'Ruby', 'composer.json': 'PHP (Composer)', 'go.mod': 'Go', 'Cargo.toml': 'Rust',
    'pubspec.yaml': 'Flutter/Dart', 'next.config.js': 'Next.js', 'next.config.mjs': 'Next.js',
    'nuxt.config.ts': 'Nuxt', 'vite.config.ts': 'Vite', 'vite.config.js': 'Vite',
    'astro.config.mjs': 'Astro', 'svelte.config.js': 'SvelteKit', 'prisma/schema.prisma': 'Prisma ORM',
    'supabase/': 'Supabase', 'migrations/': 'SQL migrations folder', '.github/workflows/': 'GitHub Actions (CI/deploy)',
    'CLAUDE.md': 'existing CLAUDE.md (read it first)', 'AGENTS.md': 'existing AGENTS.md (read it first)',
}
TEST_RE = re.compile(r'(^|/)(tests?|__tests__|spec)/|\.(test|spec)\.[a-z]+$')

SECRETS = [
    ('private key', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('AWS access key', re.compile(r'AKIA[0-9A-Z]{16}')),
    ('GitHub token', re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}')),
    ('Slack token', re.compile(r'xox[abprs]-[A-Za-z0-9-]{10,}')),
    ('Google API key', re.compile(r'AIza[0-9A-Za-z_-]{35}')),
    ('Stripe live key', re.compile(r'(sk|rk)_live_[0-9A-Za-z]{16,}')),
    ('API key (sk-)', re.compile(r'\bsk-[A-Za-z0-9_-]{20,}')),
    ('JWT', re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.')),
    ('connection string with password', re.compile(r'[a-z+]+://[^/\s:@]+:[^/\s:@]{3,}@')),
    ('assigned secret', re.compile(r'(?i)(password|passwd|secret|api[_-]?key|token|auth)["\']?\s*[:=]\s*["\'][^"\'\s]{12,}["\']')),
]


def files_of(repo):
    out = subprocess.run(['git', 'ls-files'], cwd=repo, capture_output=True, text=True)
    if out.returncode:
        sys.exit('not a git checkout: ' + repo)
    return [f for f in out.stdout.splitlines() if f]


def readable(f):
    low = f.lower()
    return not (low.endswith(SKIP_EXT) or os.path.basename(f) in LOCKS
                or any(d in '/' + low for d in SKIP_DIRS))


def secrets_in(path, label):
    hits = []
    try:
        with open(path, errors='ignore') as fh:
            for n, line in enumerate(fh, 1):
                for kind, rx in SECRETS:
                    if rx.search(line):
                        hits.append(f'{label}:{n}  {kind}')
                        break
    except OSError:
        pass
    return hits


def scan(repo):
    all_files = files_of(repo)
    files = [f for f in all_files if readable(f) and not f.startswith(('docs/claude/', '.claude/'))]
    print(f'# scan of {os.path.abspath(repo)}')
    print(f'tracked files: {len(all_files)} (readable source: {len(files)})')

    top = Counter(f.split('/')[0] + ('/' if '/' in f else '') for f in files)
    print('\n## layout (top level, readable files)')
    print('  ' + ' · '.join(f'{k} {v}' for k, v in top.most_common(15)))

    stats = []
    for f in files:
        try:
            with open(os.path.join(repo, f), errors='ignore') as fh:
                lines = fh.read().split('\n')
        except OSError:
            continue
        stats.append((f, len(lines), max((len(l) for l in lines), default=0)))

    big = sorted((s for s in stats if s[1] > 150), key=lambda s: -s[1])[:20]
    print('\n## big files (>150 lines, largest first): read by range, never whole')
    print('  ' + (' · '.join(f'{f} {n}' for f, n, _ in big) or 'none'))

    longl = sorted((s for s in stats if s[2] > 500), key=lambda s: -s[2])[:12]
    print('\n## very long lines (>500 chars): always cut grep output, e.g. | cut -c1-200')
    print('  ' + (' · '.join(f'{f} {m}' for f, _, m in longl) or 'none'))

    print('\n## platform hints')
    seen = set()
    for key, hint in HINTS.items():
        found = any(f == key or f.endswith('/' + key) for f in all_files) if not key.endswith('/') \
            else any(('/' + key) in '/' + f for f in all_files)
        if found and hint not in seen:
            seen.add(hint)
            print(f'  {key} -> {hint}')
    if not seen:
        print('  none detected: ask the owner how the project runs and deploys')

    tests = [f for f in files if TEST_RE.search(f)]
    print(f'\n## tests: {len(tests)} test files' + (f' (e.g. {tests[0]})' if tests else ' (no test suite)'))

    never = sorted({d.strip('/') for f in all_files for d in SKIP_DIRS if d in '/' + f.lower()})
    locks = sorted({os.path.basename(f) for f in all_files if os.path.basename(f) in LOCKS})
    print('\n## never open: ' + (' · '.join(never + locks) or 'nothing special') + ' · binary media')

    hits = []
    for f in files:
        hits += secrets_in(os.path.join(repo, f), f)
    print(f'\n## possible secrets in tracked files: {len(hits)}' + (' (values not shown)' if hits else ''))
    for h in hits[:20]:
        print('  ' + h)
    if hits:
        print('  -> never copy these into any skill or doc; tell the owner to rotate real keys')


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--secrets':
        found = []
        for p in sys.argv[2:]:
            found += secrets_in(p, p)
        print('\n'.join(found) if found else 'no secrets found')
        sys.exit(1 if found else 0)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    scan(sys.argv[1])
