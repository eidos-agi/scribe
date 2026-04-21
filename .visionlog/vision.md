---
title: "Scribe \u2014 the per-repo documentarian"
type: "vision"
date: "2026-04-21"
---

Every eidos repo has a team of agents — stepproof enforces the plan, lighthouse navigates toward a north star, hone self-improves over time. Scribe is the teammate whose job is to keep the repo's authoritative self-description current. When any other tool modifies a repo, it calls scribe so the card reflects what the repo IS now, not what it was three sessions ago.

Scribe is deliberately dumb. It does not synthesize. It does not run an LLM. It is a data layer — three tools (init, read, update) that store a card and log every change. The intelligence of writing a good tool card lives in the calling tool's ceremony, because that ceremony has the session context that caused the change.

Scribe is NOT a registry. Scribe is NOT a search engine. Scribe is NOT cross-repo. It is vertical — one scribe per repo, living in .scribe/, indexed later by omni for cross-repo search.

The product: every eidos repo has a fresh, authoritative card at a known path. No stale documentation, no drift between what a tool IS and what other agents think it is. When someone asks "what is hone for?" omni returns the answer because hone's scribe kept the card current.
