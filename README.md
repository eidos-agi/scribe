# scribe

The per-repo documentarian. Scribe is the teammate every other tool
calls when it has just changed a repo — *"you just modified me, update
my self-description so the outside world still knows what I am."*

## What scribe is

A small MCP. Three tools. Data-layer only — no LLM synthesis inside
scribe. The *intelligence* of writing a good tool card lives in the
calling tool's ceremony; scribe just stores, reads, and logs changes.

```
<repo>/.scribe/
  card.md          # the authoritative tool card (markdown + YAML frontmatter)
  updates.jsonl    # append-only log of every change that touched the card
```

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

## MCP tools

- `scribe_init(repo)` — set up `.scribe/` in the target repo (creates
  the directory + a minimal card.md if one doesn't exist)
- `scribe_read(repo)` — return the current card plus the last N
  entries from updates.jsonl
- `scribe_update(repo, change_summary, new_card?=None)` — record the
  change in updates.jsonl; if `new_card` is provided, overwrite
  card.md atomically

## How other tools use it

At the end of any ceremony that landed a real change, the tool calls
scribe_update. Example, from hone's Retain phase:

```
# after a successful hone tick on target=X:
mcp__scribe__scribe_update(
  repo=X,
  change_summary="Shrunk ceremony from 10 phases to 4",
  new_card=<synthesized by the agent from old card + change>,
)
```

Scribe itself does zero synthesis — but because the call happens
*during* the session that caused the drift, the agent has full
context to write a fresh card. No stale, no drift, no lag.

## Why scribe, why not omni

omni is the cross-repo memory/search layer. It indexes across
everything. scribe is per-repo, vertical, authorial. They work
together: scribe keeps each repo's card fresh; omni indexes the
union of all repos' cards so any agent can search "what tool does
X?" and get the right answer.

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
