---
id: "ADR-001"
type: "decision"
title: "ADR-001: Scribe is data-layer only, not a synthesizing agent"
status: "accepted"
date: "2026-04-21"
---

## Context
When designing scribe, a natural temptation is to make scribe_update "smart" — take a change summary + current card, call an LLM, synthesize a new card. That would make callers simpler (they just describe the change; scribe figures out the edit).

## Decision
Scribe has no LLM synthesis. Callers synthesize; scribe stores + logs.

## Reasons
1. The caller has session context that scribe never will. When hone's Retain phase calls scribe, hone has seen the diff, the measurement before/after, the agent's diagnosis. Scribe running its own LLM would be guessing from a change_summary string, which is always lossier than the caller's view.
2. Synthesis-in-scribe means every scribe_update costs LLM tokens. Synthesis-in-caller means the tokens are spent only when needed, and only by the tool that already has the context loaded.
3. Data-layer tools compose. A dumb store + log API is easy to call from anywhere (CLI, cron, other MCPs, test fixtures). An LLM-synthesizing tool is a heavier dependency.

## Consequences
- Callers must write their own card-synthesis prompts. Scribe documents the expected card format (YAML frontmatter + markdown body) but does not enforce it.
- A caller that forgets to synthesize will leave the card stale until someone else updates it. That is a caller bug, not a scribe bug — surfaced by scribe_read showing a recent update with card_written=false.
- Scribe remains tiny: ~150 lines of code, three tools, no API keys, no model selection, no prompt library.
