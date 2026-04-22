---
name: scribe
version: 0.0.1
license: Apache-2.0
github_url: https://github.com/eidos-agi/scribe
visibility: public
one_liner: Per-repo documentarian MCP. Keeps a repo's authoritative self-description current as other tools change it.
when_to_reach_for:
  - You are a tool that just modified a repo — call scribe_update so the card reflects what the repo IS now
  - You need to know what a repo does at a glance — scribe_read returns the card
  - You are starting a new repo and want scribe-tracked self-description — scribe_init
  - You are a card author and want consistent teammate names — scribe_team returns the 12-entry roster
invoke:
  - mcp__scribe__scribe_init(repo)
  - mcp__scribe__scribe_read(repo, recent=10)
  - mcp__scribe__scribe_update(repo, change_summary, new_card?, author_tool?)
  - mcp__scribe__scribe_team()
capabilities:
  - Create .scribe/ in any repo (idempotent)
  - Read card + last N update log entries
  - Atomically overwrite card.md + append to updates.jsonl
  - Expose team roster (src/scribe/team.yaml, 12 entries)
  - Hot-reload on every MCP call (importlib.reload pattern; no restart needed for code edits)
not_capabilities:
  - Cross-repo anything (omni does that)
  - LLM synthesis (ADR-001 — the caller has better context)
  - Enforcement / blocking (stepproof does that)
guardrails:
  - No LLM synthesis inside scribe (GUARD-001)
  - One scribe per repo, never cross-repo (GUARD-002)
  - Every update must be logged, even when card.md is not written (GUARD-003)
adrs:
  - ADR-001 (accepted): Scribe is data-layer only, not a synthesizing agent
layout:
  - .scribe/card.md — the authoritative tool card (this file)
  - .scribe/updates.jsonl — append-only log of every change
install:
  - clone: git clone https://github.com/eidos-agi/scribe.git ~/repos-eidos-agi/scribe
  - sync: cd ~/repos-eidos-agi/scribe && uv sync
  - register: claude mcp add scribe --scope user -- /path/to/scribe/.venv/bin/scribe
teammates_known: hone, scribe, stepproof, lighthouse, ike, visionlog, research-md, omni, loss-loop, improve-forge, learning-forge, mcp-self-report
mcp_tools: 4
updated_by: hone-tick-2026-04-22T025202Z
---

# scribe

The per-repo documentarian. Point other tools at scribe after they modify a repo; scribe keeps the repo's self-description current.

Public at **https://github.com/eidos-agi/scribe** · Apache-2.0 · Alpha v0.0.1.

## The discipline

Scribe is deliberately small. Four MCP tools, ~200 lines of code, no LLM inside. The value is disciplinary: when hone or stepproof or lighthouse land a change, they MUST call scribe_update in the same ceremony — that is what keeps the card fresh. A tool that forgets is the bug, not scribe.

## How the team uses scribe

```
hone ceremony lands a change     →  scribe_update(repo=target, change_summary=..., new_card=synthesized)
stepproof completes a run         →  scribe_update(repo=state.target, change_summary=verified evidence)
lighthouse promotes a pattern     →  scribe_update(repo=repo_path, change_summary=pattern promoted)
```

Omni indexes all .scribe/ dirs across repos for cross-repo search.

## Why not smarter

See ADR-001. Every extra gram of intelligence inside scribe is intelligence stolen from the caller — and the caller has session context scribe cannot reconstruct. Keeping scribe data-layer only makes it composable from anywhere (CLI, cron, other MCPs, tests) and prevents the creeping feature-set that turns a data tool into a flaky agent.