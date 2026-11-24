---
name: repo-skill-forge
description: Builds a lean, project-specific skill for one repository - a short SKILL.md with the owner's rules and red lines, plus feature reference docs read only on demand and a monthly audit script - so every coding session starts knowing the project while loading far fewer tokens. Use when the user asks to create, build, slim down, rebuild or audit a skill (or CLAUDE.md) for their repo, project, codebase or site.
---

# repo-skill-forge

You build a **per-repo skill**: the project's memory for Claude. Every session in that repo then starts with the map, the rules and the red lines, without re-reading the codebase or re-explaining decisions.

The design follows three findings about agent memory:
- **Keep the always-loaded layer small.** Long instruction files cost tokens every session and lower adherence. SKILL.md holds only what every task needs; feature details sit one level down.
- **Progressive disclosure.** Details live in small reference files that are read only when a task touches that feature.
- **Memory goes stale.** A periodic audit (the "dreaming" pass) checks every name the docs mention against the code and proposes fixes for the owner to approve.

## Output

| Piece | Where | Loaded |
|---|---|---|
| `SKILL.md` (aim 8-15 KB) | the user's Claude skills | every session in the repo |
| `docs/claude/<area>.md` (4-8 files, each under 6 KB) | see "Mode" below | only when a task touches that area |
| `audit.py` | next to the docs | only when the owner asks for an audit |

Write the skill in the language the owner writes to you in. Templates: `templates/SKILL.template.md` (English) and `templates/SKILL.template.ar.md` (Arabic). Reference-file format: `templates/doc.template.md`.

## Step 1. Privacy gate (always first)

Reference docs describe the code in detail: routes, tables, limits, security checks. In a public repository that is a map for attackers. Find out the visibility before writing anything:
- `gh repo view OWNER/REPO --json visibility -q .visibility`, if `gh` is signed in; or
- `curl -s -o /dev/null -w '%{http_code}' https://api.github.com/repos/OWNER/REPO`: `200` means anyone can see it (public); `404` means private or missing (the owner can still clone it: private).
- Other hosts, or no answer: ask the owner.

Then pick the **mode**:
- **Mode A, private repo (recommended):** docs go in the repo at `docs/claude/` and are versioned with the code. Every commit that changes a feature updates its doc in the same commit.
- **Mode B, public repo, unknown visibility, or the owner prefers it:** nothing is written into the repo. Docs go next to SKILL.md in the skill folder (`references/`). The owner uploads the folder as a ZIP (claude.ai) or keeps it in `~/.claude/skills/<name>/` (Claude Code, outside the repo).

Say which mode you chose and why in one line. Never switch a repo to Mode A because the owner says it "will be private later".

## Step 2. Cheap scan

Run `python3 scripts/scan.py REPO` (path relative to this skill's folder). In a few hundred tokens it reports the layout, big files, very long lines, platform hints (deploy, database, CI), test presence, folders never to open, and possible secrets (location and kind only).
- If the repo has `CLAUDE.md` or `AGENTS.md`, read it: its rules move into the new SKILL.md.
- If the owner already has a long skill for this repo, this is a **slim-down**: run `scripts/audit.py` on it first (Step 6 shows how) so stale entries are dropped, not copied.
- Possible secrets: never copy them anywhere. Tell the owner to rotate any real key that is committed.

## Step 3. Ask the owner (one message, at most five questions)

Skip any question the scan or the conversation already answers.
1. What is the project, in one line? Who uses it?
2. Red lines: things that must never change or break (data, quality, privacy, cost limits, design).
3. Should Claude explain a plan and wait for approval before changes, or act and report?
4. How are changes delivered? (push to main deploys? pull requests? manual deploy?)
5. Which features do you work on most? (They get the clearest docs.)

## Step 4. Map the features

Group the code into 4-8 **areas** the way the owner thinks about the project (e.g. pages, uploads, notifications, admin, data). For each area find, with `grep -n … | cut -c1-200` and short ranged reads only (never whole big files):
- the files, in the order a change flows: server → client → styles;
- key functions, routes, tables and columns;
- decisions and gotchas the code does not show (why something is done a certain way, a past bug, a measured performance lesson).

Write one line per feature, every file, function, column and route in backticks (the audit relies on backticks). Each area file under 6 KB. Facts only, no history ("removed last month" belongs nowhere). Data model and migration rules go in their own area file (`data.md`).

## Step 5. Write SKILL.md

Fill the template. Keep in SKILL.md only what **every** task needs:
- the start command (clone or pull, plus the first grep), reading and editing rules filled with the scan's real big files and long lines;
- the behaviour rules from the template, unchanged unless the owner asks;
- how the project is built (3-6 bullets: the patterns every change uses);
- the index of docs files, one line each, saying when to read it;
- the data rule in two lines, red lines, delivery command, audit section.

Everything else goes to docs. If SKILL.md passes 15 KB, move detail down; never cut a red line or a behaviour rule to save space. The behaviour rules carry an attribution line (MIT): keep it.

## Step 6. Check before delivering

1. `python3 scripts/scan.py --secrets SKILL.md DOCS/*.md`: must print `no secrets found`. No keys, passwords, tokens or connection strings in any form. In Mode B also leave out security thresholds and admin URLs.
2. Copy `scripts/audit.py` next to the docs, then run `python3 DOCS/audit.py --repo REPO --docs DOCS --skill SKILL.md`. Stale names must be `none`: fix the docs, or list words that are commands or tool names (not code) in the skill's `<!-- audit-ignore: … -->` line. Undocumented files: add the ones a task could touch; leave trivial ones (404 pages, icons).
3. Measure honestly: bytes of what used to load every session (old skill or CLAUDE.md, if any) against SKILL.md plus one typical doc.

## Step 7. Deliver (with the owner's approval)

Show the file list, sizes and the mode, then wait for a yes.
- **Mode A:** commit `docs/claude/` (docs plus `audit.py`) in one commit that touches no code. If pushing deploys the project, say that it redeploys unchanged code.
- **SKILL.md:** in claude.ai, offer it for the owner to save as a skill (or upload as a ZIP); in Claude Code, `.claude/skills/<name>/SKILL.md` (Mode A may commit it there) or `~/.claude/skills/<name>/`.
- Tell the owner two habits: ask Claude in a fresh chat to work as usual and check that it opens only the right doc; and once a month say "audit the skill".

## Audit mode ("audit my skill")

Study only, no edits: run `audit.py` with `--repo`, `--docs` and `--skill`, then present a short list: stale (remove), missing (add), each with evidence from the code. Apply nothing before the owner approves. After approval, Mode A changes ship as one docs-only commit; SKILL.md changes are offered for the owner to save.

## Never

- Write docs into a public repo, or any secret into any file.
- Change the project's code while building its skill.
- Copy a whole file, long config or long code into docs: point to it.
- Invent rules the owner did not give. Ask, or leave the section short.
