# scribe

[![CI](https://github.com/eidos-agi/scribe/actions/workflows/ci.yml/badge.svg)](https://github.com/eidos-agi/scribe/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

**Technical writer for your repo.** Scribe authors and curates the docs that
tell the project what it is — the card, the README, the CHANGELOG, the skill
files, anything. When the code changes, scribe makes the documentation move
with it so the repo's self-description never drifts.

## What scribe is

An MCP server. Three tools today (v0.0.1), heading to five (v0.1.0 per
visionlog ADR-004). Storage + log is atomic. Authoring happens via the
calling agent or through scribe delegating to `claude -p` — no direct
Anthropic SDK use, ever.

```
<repo>/.scribe/
  card.md           # authoritative tool card (markdown + YAML frontmatter)
  updates.jsonl     # append-only log of every change that touched the repo's docs
  scribe.yaml       # v0.1.0 — lists which paths scribe treats as tracked docs
```

## Status

- **v0.0.1 — shipped.** Narrow data layer. Single file (`card.md`). No
  synthesis. Current public release.
- **v0.1.0 — planned.** Path-generic API, `scribe_review`, `scribe_suggest`,
  `scribe.yaml` config, supersedes ADR-001. See `.visionlog/adr/ADR-004-*`
  and `.ike/tasks/TASK-0005-*`.

## The team

Each eidos repo has a team of agents living in it:

```
~/repos-eidos-agi/<repo>/
  .stepproof/     enforces the plan
  .lighthouse/    navigates toward the north star
  .hone/          self-improves over time
  .scribe/        keeps the self-description current          ← this one
  …
```

scribe is the teammate nobody remembers to be, which is exactly the
reason tool cards go stale everywhere else.

## MCP tools (v0.0.1)

- `scribe_init(repo)` — set up `.scribe/` in the target repo (creates
  the directory + a minimal card.md if one doesn't exist)
- `scribe_read(repo)` — return the current card plus the last N
  entries from updates.jsonl, plus a `callers_seen` list
- `scribe_update(repo, change_summary, new_card?=None)` — record the
  change in updates.jsonl; if `new_card` is provided, overwrite
  card.md atomically

## v0.1.0 additions (planned — ADR-004)

- `scribe_update(repo, path, change_summary, new_content?, author_tool?)` —
  **breaking change**: `path` is now explicit. Any file under the
  repo, not just `.scribe/card.md`.
- `scribe_review(repo)` — coherence pass: returns a list of tracked
  docs that look stale relative to recent code changes.
- `scribe_suggest(repo, change)` — given a code-change description,
  delegates to `claude -p` to return a ranked list of docs that
  should move, with reasoning.
- `.scribe/scribe.yaml` — caller-editable list of paths scribe
  treats as tracked (card.md, README.md, CHANGELOG.md, `docs/*`,
  `.claude/skills/*.md`).

## How other tools use it

When an agent ships a code change, it calls scribe for the doc
updates that should move with it. In v0.0.1 this is card-only. In
v0.1.0 scribe covers the full repo surface:

```
# after a successful code change
mcp__scribe__scribe_suggest(repo=X, change="added user_preferences table")
  → ["README.md#data-layer", "CHANGELOG.md", ".scribe/card.md"]

# then for each:
mcp__scribe__scribe_update(repo=X, path="README.md",
  change_summary="data layer: 2 → 3 tables",
  new_content=<synthesized by the caller or by claude -p>,
  author_tool="agent-7")
```

Synthesis happens in a session with real context — either the
calling agent's own session or a scribe-spawned `claude -p`. Scribe
itself never imports the Anthropic SDK.

## Why scribe, why not omni

omni is the cross-repo memory/search layer. It indexes across
everything. scribe is per-repo, vertical, authorial. They work
together: scribe keeps each repo's card fresh; omni indexes the
union of all repos' cards so any agent can search "what tool does
X?" and get the right answer.

## Improving scribe via hone

This repo ships a `.mcp.json` that registers **hone** via uvx-from-git.
Clone the repo, open it in Claude Code, and `hone scribe` just works
— hone is fetched from `github.com/eidos-agi/hone` on first use and
runs in a uvx-managed venv. No separate install step needed.

```bash
git clone https://github.com/eidos-agi/scribe
cd scribe
claude      # open Claude Code here; hone auto-registers from .mcp.json
# then in the Claude session:
/loop 15m hone
```

## Install

```bash
cd ~/repos-eidos-agi/scribe
uv sync
```

Register at user scope:

```bash
claude mcp add scribe --scope user -- /Users/you/repos-eidos-agi/scribe/.venv/bin/scribe
```

## Status

Alpha. v0 ships the three-tool data layer. No smart regeneration,
no stale detection, no diff tracking — those features land when
they're earned by real use, not speculation.
