# Changelog

All notable changes to scribe are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.0.1] — 2026-04-22

First public release.

### Added

- `scribe_init(repo)` — create `.scribe/` in any repo. Idempotent.
- `scribe_read(repo, recent=10)` — return the current card plus the last N update-log entries.
- `scribe_update(repo, change_summary, new_card?, author_tool?)` — append to `updates.jsonl`; optionally overwrite `card.md` atomically.
- `scribe_team()` — expose the 12-entry roster of eidos tools (8 MCPs + 4 non-MCP tools).
- Data layout per repo: `.scribe/card.md` (YAML frontmatter + markdown body) and `.scribe/updates.jsonl` (append-only log).
- Hot-reload (`importlib.reload`) at every MCP tool boundary.
- Visionlog project with 3 guardrails (GUARD-001 no LLM inside, GUARD-002 never cross-repo, GUARD-003 always log) and 3 ADRs.
- Lighthouse north star `ns_c5a90a5cc690` — "reliably consulted by other tools when they modify a repo".
- 9 smoke tests (pytest) covering card I/O, team roster validation, and a static-scan regression test enforcing ADR-001 (no LLM SDK imports).
- GitHub Actions CI running tests on push + PR + workflow_dispatch.
- `.mcp.json` that registers hone via `uvx --from git+` so cloners get plug-and-play improvement tooling.
- Apache-2.0 LICENSE.

### Design decisions recorded as ADRs

- **ADR-001** Scribe is data-layer only, not a synthesizing agent. No LLM inside scribe.
- **ADR-002** Team roster is a static shipped yaml, not runtime discovery.
- **ADR-003** Card format is YAML frontmatter + markdown body.

### Not in v0.0.1

- Stale detection
- Diff tracking of cards over time
- Auto-regeneration of cards

Those land when real use justifies them, not on speculation.

[0.0.1]: https://github.com/eidos-agi/scribe/releases/tag/v0.0.1
