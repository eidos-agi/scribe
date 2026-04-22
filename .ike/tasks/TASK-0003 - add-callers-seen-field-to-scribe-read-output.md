---
id: TASK-0003
title: Add "callers seen" field to scribe_read output
status: To Do
created: '2026-04-21'
priority: low
tags:
  - feature
acceptance-criteria:
  - scribe_read returns a callers_seen list
  - test covering the aggregation
---
Tick 17's delta: scribe_read currently returns card + recent update entries. Add a derived field showing distinct author_tools that have ever called scribe_update for this repo — so repo owners can see "who's been updating my card" at a glance. Purely derived from updates.jsonl, no new storage.
