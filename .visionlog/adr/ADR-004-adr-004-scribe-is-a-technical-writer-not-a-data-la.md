---
id: "ADR-004"
type: "decision"
title: "ADR-004: Scribe is a technical writer, not a data layer \u2014 supersedes ADR-001"
status: "accepted"
date: "2026-04-22"
supersedes: "ADR-001"
---

## Context
Scribe v0.0.1 shipped as a narrow data-layer MCP: store a card at `.scribe/card.md`, log updates to `.scribe/updates.jsonl`, no LLM synthesis (ADR-001). That framing made scribe small, composable, and honest — but it also made scribe boring. When Daniel saw the tool page, the direct feedback was: "scribe is about intelligent authoring and curation — technical writing and project coherence." The data-layer framing doesn't sell what scribe should be.

The bigger product is: scribe is the teammate that keeps all of a repo's documentation truthful as the code changes. It authors updates to README, CHANGELOG, the card, skill files, `docs/*` — any surface that tells the project what it is. When an agent ships a code change, scribe detects which docs went stale and writes the coherent diffs for each.

## Decision
Scribe is a **technical writer + documentation curation layer**, not just a data store. Supersede ADR-001.

## What changes
1. **API surface**: generalized from single-file to any file.
   - Old: `scribe_update(repo, change_summary, new_card?, author_tool?)` — card-only.
   - New: `scribe_update(repo, path, change_summary, new_content?, author_tool?)` — any file path inside the repo.
2. **New tools**:
   - `scribe_review(repo)` — coherence pass; returns which tracked docs look stale relative to the code.
   - `scribe_suggest(repo, change_description)` — given a code change, returns which docs should move and why.
3. **Agent delegation permitted**: scribe may invoke `claude -p` (or similar subscription-tool orchestration) to author or review prose. Still no direct Anthropic SDK use — subscription tooling only, per the broader eidos CLAUDE.md constraint.
4. **Storage remains atomic**: write + log pattern unchanged; tmp-file + os.replace; O_APPEND + fsync for updates.jsonl. The "how" stays boring; the "what" expands.

## Reasons
1. The narrow framing doesn't sell. The page mockup had to go aspirational on the website to convey scribe's real value — implementation should catch up.
2. A per-repo card by itself is insufficient — README, CHANGELOG, skills, and docs are where agents and readers actually look. A documentarian that only touches one file of that universe leaves 90% of the drift unaddressed.
3. The agent-delegation pattern (calling `claude -p`) keeps scribe's process simple (it doesn't hold conversation state, doesn't pay per-token). It also keeps scribe honest — synthesis still happens in an ephemeral agent session, not a long-lived server.

## Guardrail updates
- GUARD-001 ("no LLM synthesis inside scribe") → loosened: scribe may delegate synthesis to `claude -p` / claude_agent_sdk, but still does not import the Anthropic SDK directly. The data-layer test (`test_no_llm_sdk_imports_in_source`) remains: scans for banned SDK imports.
- GUARD-002 ("never cross-repo") → unchanged. Scribe is still vertical — one repo at a time.
- GUARD-003 ("always log updates") → unchanged and still a regression test.
- New GUARD-004 (add in this same ADR): "Scribe never runs synthesis without a tracked change_summary." The change_summary is the human-legible record of why the write happened.

## Consequences
- `scribe_update` breaking change. Bump to v0.1.0.
- Existing callers (hone's Retain-4b, when it's re-enabled) need to pass `path=".scribe/card.md"` explicitly.
- Test suite grows: tests for path-generic update, `scribe_review`, `scribe_suggest`.
- CHANGELOG.md on scribe repo needs a new `[0.1.0]` entry.
- The tool page on eidosagi.com (already updated as aspirational) now has matching implementation.
- ADR-001 marked as SUPERSEDED in visionlog.

## Supersedes
ADR-001 (Scribe is data-layer only, not a synthesizing agent). ADR-001 stays on file as historical record — it was correct for v0.0.1's scope, and the lesson it encoded (don't hold LLM state inside the server) carries forward via the "subscription tooling only" clause above.
