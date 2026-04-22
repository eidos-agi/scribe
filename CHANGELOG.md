# Changelog

All notable changes to scribe are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.3] — 2026-04-22 — ADR-004 complete

### Added

- `scribe_suggest(repo, change, tracked?)` — ranked-doc recommender. Given a code-change description, returns which tracked docs need updates, with reasoning. Delegates to `claude -p` via subprocess (no Anthropic SDK import — subscription tooling only, per ADR-004). Prompt template lives in `card.py::_SUGGEST_PROMPT`; output is balanced-JSON-extracted so prose wrappers and ```fence blocks survive. Filters out any suggested path not in the tracked list (no hallucinated docs).
- Graceful degradation — never raises. Returns status ∈ `{ok, claude-unavailable, timeout, parse-error}` with an explanatory `message` field for the non-ok cases.
- 3 new tests using `monkeypatch.setattr(subprocess, "run", ...)` so the suite runs without the `claude` binary: claude-unavailable path, canned JSON parse, JSON extraction from prose wrapper.

### ADR-004 status: 4 of 4 core features shipped

- v0.1.0 — path-generic `scribe_update`
- v0.1.1 — `scribe_review` coherence pass
- v0.1.2 — `.scribe/scribe.yaml` config
- **v0.1.3 — `scribe_suggest` — this release**

Scribe is now a real technical writer: path-generic writes + review + config + delegation. All synthesis happens in a `claude -p` subprocess or in the calling agent's own session — scribe itself stays data-layer-clean (still zero LLM SDK imports; `test_no_llm_sdk_imports_in_source` still passes).

[0.1.3]: https://github.com/eidos-agi/scribe/releases/tag/v0.1.3

## [0.1.2] — 2026-04-22

### Added

- `.scribe/scribe.yaml` — caller-editable config listing which repo-relative paths scribe treats as tracked docs. Schema v0 has a single `tracked: list[str]` field. `scribe_init` now writes a default scribe.yaml if one doesn't exist (adds `.scribe/card.md`, `README.md`, `CHANGELOG.md` out of the gate).
- `card.load_config(repo)` — loads and validates scribe.yaml; fails open to `{}` when missing, unparseable, or PyYAML unavailable.
- `scribe_review` now prefers the repo's `scribe.yaml#tracked` list when present; falls back to hardcoded defaults otherwise. `scribe_suggest` (future tick) will use the same source.
- pyyaml re-added as a dep (was removed in v0.0.2 after team.yaml was deleted).
- 2 new tests: scribe_init creates the yaml with defaults; scribe_review reads the yaml's override list.

### Changed

- `scribe_init` return value adds `config_path` and `config_created`.
- Init log entry in updates.jsonl now records `created_config` alongside `created_card`.

### ADR-004 status

**3 of 3 core features now shipped:** path-generic `scribe_update` (v0.1.0), `scribe_review` (v0.1.1), `scribe.yaml` (this release). The remaining ADR-004 sub-feature is `scribe_suggest(repo, change)` — the `claude -p`-delegated ranked-doc recommender.

[0.1.2]: https://github.com/eidos-agi/scribe/releases/tag/v0.1.2

## [0.1.1] — 2026-04-22

### Added

- `scribe_review(repo, tracked?)` — coherence-pass tool that flags tracked docs whose last git-touch predates the most recent non-doc commit. Returns per-path `{status, reason, doc_last_touch, code_last_touch}` with status ∈ `{stale, fresh, unknown}`. Default tracked list: `.scribe/card.md`, `README.md`, `CHANGELOG.md`. Implementation walks `git log --follow` for each doc and compares ISO timestamps against the newest non-doc commit. Fails open — returns `unknown` when git is unavailable or the path has no history.
- 3 new tests covering stale-vs-fresh-vs-unknown paths.

### Still pending (ADR-004)

- `scribe_suggest(repo, change)` — `claude -p` delegation for ranked-doc recommendations.
- `.scribe/scribe.yaml` — caller-editable tracked-doc list (replaces the hardcoded default).

[0.1.1]: https://github.com/eidos-agi/scribe/releases/tag/v0.1.1

## [0.1.0] — 2026-04-22

Pivot to "technical writer" framing per ADR-004 (supersedes ADR-001).
**Breaking change** to `scribe_update` signature — callers that pass
only `change_summary` + `new_card` still work via a compat shim, but
the documented API is now path-generic.

### Added

- `scribe_update` accepts a `path` argument (repo-relative, default `.scribe/card.md`). Any file under the repo can be the destination — README.md, CHANGELOG.md, .scribe/card.md, docs/*, .claude/skills/*.md, etc.
- `scribe_update` accepts `new_content` as the canonical argument name for the file body. `new_card` remains as a v0.0.1 alias.
- `updates.jsonl` records `path` + `file_written` on every entry; `card_written` is preserved for backward-compat readers.
- Return value from `scribe_update` includes `path`, `full_path`, `file_written` (v0.1.0) alongside `card_written` / `card_path` (v0.0.1 compat).
- 3 new tests covering path-generic writes, multi-path log entries, and the v0.0.1 backward-compat shim.

### Changed

- `src/scribe/card.py update()` signature changed to `(repo, change_summary, path=".scribe/card.md", new_content=None, author_tool=None, new_card=None)`.
- `ADR-001` in visionlog marked **superseded** by `ADR-004`.
- README rewritten to describe scribe as a technical writer; v0.0.1 vs v0.1.0 status split.

### Not yet in v0.1.0 (ADR-004 scope, future ticks)

- `scribe_review(repo)` — coherence-pass tool returning stale docs.
- `scribe_suggest(repo, change)` — delegates to `claude -p` for ranked-doc recommendations.
- `.scribe/scribe.yaml` config for the tracked-doc list.

[0.1.0]: https://github.com/eidos-agi/scribe/releases/tag/v0.1.0

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
