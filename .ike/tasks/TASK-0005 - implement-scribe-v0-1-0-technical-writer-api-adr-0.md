---
id: TASK-0005
title: Implement scribe v0.1.0 — technical writer API (ADR-004)
status: To Do
created: '2026-04-22'
priority: high
tags:
  - feature
  - breaking-change
  - v0.1.0
---
Ships the API and behavior described in visionlog ADR-004. Breaking change from v0.0.1. Split into sub-tasks when the scope becomes a milestone — keeping this single ticket to track the headline outcome.

Scope:
1. Generalize scribe_update signature: (repo, path, change_summary, new_content?, author_tool?) — path replaces the card-only implicit destination. Update updates.jsonl schema to include `path`.
2. Add scribe_review(repo) — returns a list of tracked docs that look stale (simple heuristic: last-commit-touching vs last-meaningful-code-commit, or no updates log entry since last release).
3. Add scribe_suggest(repo, change_description) — given a natural-language code-change description, delegates to claude -p to return a ranked list of doc paths that should move with reasoning. Output is read-only; the caller decides what to author.
4. Introduce a `tracked_docs` config at .scribe/scribe.yaml — lists which paths scribe considers authoritative (card.md, README.md, CHANGELOG.md, docs/*, .claude/skills/*.md). Default template ships with safe defaults.
5. Update tests: existing 8 stay (with path="card.md" where needed), add coverage for path-generic update, review, suggest.
6. Tag v0.1.0, update CHANGELOG with the breaking-change entry.
7. Update .mcp.json consumers (hone, etc.) to pass path explicitly when wiring scribe_update back in.</description>
<parameter name="acceptance_criteria">["scribe_update accepts path arg and writes to any file under the repo", "updates.jsonl records path on every entry", "scribe_review returns stale-doc list for a real repo", "scribe_suggest delegates to claude -p and returns ranked docs", ".scribe/scribe.yaml loader + default template ship with v0.1.0", "all tests pass (existing + new)", "v0.1.0 tag on origin/main", "CHANGELOG has [0.1.0] entry"]
