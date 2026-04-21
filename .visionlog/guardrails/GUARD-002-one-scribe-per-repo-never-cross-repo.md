---
id: "GUARD-002"
type: "guardrail"
title: "One scribe per repo, never cross-repo"
status: "active"
date: "2026-04-21"
---

Scribe is vertical, per-repo, per-`.scribe/`. It does not aggregate across repos. It does not expose a list_all or cross_repo_search tool. Aggregation is omni's job. Keeping scribe narrow is what lets it stay simple. A scribe that grows a cross-repo view will drift into being a worse omni.
