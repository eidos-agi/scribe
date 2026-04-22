---
id: TASK-0001
title: Tag v0.0.1 + pin .mcp.json uvx spec to the tag
status: Done
created: '2026-04-21'
priority: high
tags:
  - release
acceptance-criteria:
  - v0.0.1 tag on origin/main
  - both .mcp.json files pinned to @v0.0.1
updated: '2026-04-21'
---
Create v0.0.1 tag on main, push, update hone/.mcp.json (scribe spec) and scribe's own .mcp.json (hone spec) to pin @v0.0.1 so cloners don't get mid-flight main state.

**Completion notes:** Done in tick 25. v0.0.1 tag pushed to origin/main; .mcp.json (hone spec) pinned to @v0.0.1; commit landed on main.
