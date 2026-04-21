---
id: "GUARD-001"
type: "guardrail"
title: "No LLM synthesis inside scribe"
status: "active"
date: "2026-04-21"
---

Scribe stores and logs. The calling tool (hone, stepproof, a human session) synthesizes the new card content and hands it to scribe_update. If scribe ever grows its own LLM call, it has taken on the caller's job badly. The whole point of scribe being data-layer only is that the caller ALREADY has the session context that caused the drift — scribe doing its own synthesis would be guessing without context.
