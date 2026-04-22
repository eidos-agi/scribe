---
id: "ADR-003"
type: "decision"
title: "ADR-003: Card format is YAML frontmatter + markdown body"
status: "accepted"
date: "2026-04-21"
---

## Context
scribe's card.md needs a format that's both machine-parseable (for fields like `name`, `invoke`) and human-readable (so the card is a useful doc).

## Decision
YAML frontmatter + markdown body, delimited by `---`. Frontmatter holds structured fields; body holds human narrative.

## Reasons
1. Convention already used across the ecosystem (jekyll, hugo, obsidian). Zero learning curve.
2. Machine-parseable frontmatter → omni can index reliably. Human-readable body → works as a README without tooling.
3. Single file per repo. Simpler than separate card.yaml + card.md.

## Consequences
- Every card must have a `---` delimiter pair. scribe does not enforce schema; callers decide which fields matter.
- Bad YAML frontmatter still leaves a markdown doc — graceful degradation.
- omni can walk all `.scribe/card.md` files and parse frontmatter union for cross-repo search.

## Relates to
- ADR-001 (data-layer only): the format is set by the first caller; scribe just stores what it's given. This ADR locks in the convention.
