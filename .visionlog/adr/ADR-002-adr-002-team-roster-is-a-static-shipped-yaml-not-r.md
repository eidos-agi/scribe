---
id: "ADR-002"
type: "decision"
title: "ADR-002: Team roster is a static shipped yaml, not runtime discovery"
status: "accepted"
date: "2026-04-21"
---

## Context
scribe exposes `scribe_team()` returning the list of eidos tools. The roster could be: (a) static yaml shipped with the package, (b) dynamic discovery via `claude mcp list` or similar, (c) an external registry.

## Decision
Static yaml at `src/scribe/team.yaml`, shipped in the wheel via `force-include`. Currently 12 entries (8 MCPs + 4 non-MCP tools).

## Reasons
1. Dynamic discovery has no stable API and varies by user environment. scribe's roster would look different on every machine.
2. A static roster is editable prose — anyone can add a tool to the list without code changes, just a yaml edit + reinstall.
3. It matches GUARD-002 ("never cross-repo"). Discovery would probe the filesystem; static data doesn't.
4. Callers get consistent naming + one-liners across sessions.

## Consequences
- Roster staleness is real — adding a new MCP requires a yaml edit + reinstall. Deliberate speed bump.
- Tests `test_every_team_entry_has_required_fields` and `test_team_includes_core_eidos_mcps` enforce schema hygiene and core-member presence.

## Relates to
- ADR-001 (data-layer only): static data is more data-layer than runtime discovery.
- GUARD-002 (never cross-repo): static roster doesn't probe the filesystem.
