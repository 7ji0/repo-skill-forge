---
name: "{{skill-name}}"
description: "{{Project}}: {{one line on what it is}} (repo {{owner/repo}}). Map, working rules and red lines for changing it with the fewest tokens. Use for any change, fix or question about {{Project}}, its site or its repository."
---

# {{Project}}: {{one-line description}}
{{2-3 lines: stack, where it runs, how a change goes live (e.g. "push to main deploys automatically"), scheduled jobs, database.}}

## Goal: fewest tokens
**Start (one shell call):**
```bash
{{clone-or-pull, e.g.: cd ~ && { [ -d REPO ] && git -C REPO pull -q || git clone -q --depth 1 URL; } && cd REPO}} && grep -n 'PATTERN' FILES | cut -c1-200
```
Do not read the README or explore the tree. No task lists, sub-agents or other skills unless the change itself needs them.

**Reading:**
- Read only the files the request needs (see the map). Locate with `grep -n … | cut -c1-200`, then read just that range (at most 60 lines). Batch all greps into one shell call and all independent reads into one batch.
- Never read a whole file over 150 lines. Big files (largest first): {{big files from scan}}. When unsure: `wc -l`.
- **Very long lines** ({{long-line files from scan}}): always cut grep output with `cut -c1-200`; to see around a word inside a long line: `grep -no '.\{0,100\}PATTERN.\{0,100\}' FILE`.
- Never open: {{never-open list from scan}}.
- Never print a full `git diff`; use `git diff --stat`.

**Editing:** edit with the smallest unique snippet (part of a line is enough). For a spot on a line over 500 characters, replace from the shell with a script that asserts the old text occurs exactly once.

**Behaviour:** default is silence and action: no preamble, no narration between calls, no code summaries. A request is permission for that request only; touch nothing outside it.
- Speak before acting only when an assumption is not obvious (one line, then act), or the request is ambiguous, large or touches a red line (one question, or a short plan `1. … → verify: …`, then wait). "Study / propose / don't apply" means no edits at all.
- Before writing, list everything the change must reach (callers, routes, columns, pages that load the file) and what it could break for users (data deleted or exposed, calls that stop working). That is the scope; extra features are not.
- Least code that fully solves the request, first option that works: (1) does it need to exist? skip what wasn't asked and name it in one line; a vague request gets the smallest version that does the job (2) a function, component or pattern already in the repo, used the way its neighbours use it (3) a built-in platform or standard-library feature (4) an installed dependency; never a new one for a few lines (5) one line readable at a glance (6) otherwise the minimum code that works. If something simpler than what was asked exists, say so.
- Lazy about the solution, never about finishing: complete everything the change breaks. No abstraction, wrapper, type conversion, option, config or "for later" code nobody asked for; no error handling for impossible cases; values stay in the form the platform gives. Deletion beats addition; the shortest diff wins unless it needs decoding. If 200 lines could be 50, write 50.
- Never cut: server-side validation of anything from the client, error handling that prevents data loss, security, the red lines below, accessibility, anything the owner asked for.
- Every changed line traces to the request: don't improve adjacent code, comments or formatting; don't refactor what isn't broken; match the file's style. Mention unrelated dead code, don't delete it; remove only what your own change orphaned.
- Bug fix: grep every caller first, then fix the root cause once, in the shared code.
- Moved or merged code keeps its validation and error handling. Between equal-size options, pick the one correct on edge cases.
- Comments: one line, only the why. A shortcut with a known limit is marked `// shortcut: <limit>, <when to upgrade>`.
- If the owner says "ultra": challenge any part the need doesn't justify before building. "lite": build exactly what was asked and name the smaller option in one line.
- Verify before delivering: one grep proving the change is in place and no caller of an old name remains. {{If the repo has tests: "Run `TEST COMMAND`; a bug fix starts with a failing test." Otherwise: "For non-trivial logic (branch, loop, parsing, money or quotas, security, a new script) a quick assert check in a temp folder outside the repo, not committed."}} Trivial edits need no check.

**Final reply:** one line on what changed and in which files; a second line on what was skipped or unverified and any risk the owner must know. No code recap.

Behaviour rules adapted from Ponytail (MIT, github.com/DietrichGebert/ponytail) and Karpathy-inspired guidelines (MIT, github.com/forrestchang/andrej-karpathy-skills).

## How the project is built
- {{3-6 bullets: the patterns every change uses: where pages/routes are built, routing, shared helpers, auth/session, data access}}

## Detailed map: read only when needed
This file is short on purpose. Feature details (files, functions, tables, decisions) live in `{{DOCS}}`. Read **only** the file for the area the request touches, with `cat` in the same start call, then continue as in "Reading".
- `{{area}}.md`: {{what it covers, in the words the owner uses}}
- `data.md`: tables and columns, storage, migrations, measured performance lessons. Read it before any new or changed query.
Example: `cd … && cat {{DOCS}}/{{area}}.md && grep -n 'PATTERN' FILES | cut -c1-200`

## Data in short
{{2 lines: how the schema changes (e.g. "add a new migration, never edit an old one"), and whether production can be queried read-only and how.}}

## Red lines and owner decisions
- {{red lines and standing decisions, in the owner's words}}

## Delivery (one shell call)
```bash
{{checks, e.g. node --check FILE.js}} && git add -A && git commit -qm "short message" && git pull -q --rebase && git push -q {{remote branch}} && git log --oneline -1
```
- {{deploy note, e.g. "pushing to main deploys to production"}}
- When a change adds, moves or removes a file, table, column, route or feature: update the matching `{{DOCS}}` file **in the same commit**. Delete what is gone; never write "no longer exists". Propose an update to this SKILL.md only if a general rule here changed or a docs file was added.

## Periodic audit ("audit the skill")
Only when the owner asks; study only, no edits: `python3 {{DOCS}}/audit.py --repo . --docs {{DOCS}} --skill SKILL_PATH` (SKILL_PATH: this file, as shown in "Base directory" when the skill loads). It lists names the docs mention that no longer exist in the code, and code files no doc mentions. Present proposals (stale → remove, missing → add, with evidence) and change nothing before approval.

<!-- audit-ignore: {{tool names or commands used above that are not code names}} -->
