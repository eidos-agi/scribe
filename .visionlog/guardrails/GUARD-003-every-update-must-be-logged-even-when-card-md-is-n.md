---
id: "GUARD-003"
type: "guardrail"
title: "Every update must be logged, even when card.md is not written"
status: "active"
date: "2026-04-21"
---

updates.jsonl is the trajectory — it proves scribe was consulted when a change happened, even if the card didn't need to move. If a tool calls scribe_update and scribe silently drops the log (e.g., because no new_card was provided), the trajectory is broken. Log first, write card optional.
