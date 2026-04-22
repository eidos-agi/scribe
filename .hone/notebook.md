# Hone notebook — scribe

Accumulated learnings, newest at top.

## 2026-04-22T022205Z — improved
Tick 17 exercised scribe's measure.cmd from scribe/.hone/hone.yaml for the first time — queued since tick 10. The Bash invocation parsed updates.jsonl and produced a real numeric signal: 2 distinct non-cli callers (hone, hone-session), 6 total updates. That's direct evidence the yaml→bash→signal pipeline works end-to-end for any target that declares a measure command. Separately, synthesized a fresh scribe card: added github_url (public at https://github.com/eidos-agi/scribe), visibility=public, the measure_snapshot from this tick, and a working install sequence (clone + sync + mcp add) that outsiders can actually follow. Also noted license: (none yet — add before external use) in the frontmatter — a real gap for a public repo. Card went from 36 lines to 59 lines of frontmatter carrying the full v0.0.1 state.

Full turn: [`turns/2026-04-22T022205Z.md`](turns/2026-04-22T022205Z.md)
## 2026-04-21T210717Z — improved
Bridged visionlog → hone.yaml for scribe. Read scribe's three guardrails (GUARD-001 no LLM synthesis, GUARD-002 never cross-repo, GUARD-003 always log) and its vision via visionlog MCP (project_id 7beefb4e), then wrote scribe/.hone/hone.yaml that mirrors them plus two additional hone-level guardrails ("keep scribe small" and "don't break scribe_init/read/update signatures"). Now every hone tick on target=scribe surfaces the visionlog contracts into its ceremony prompt as hard constraints. Also declared the bound instruments (visionlog=true, lighthouse=true) so the ceremony's instruments note correctly tells the agent those MCPs are available. Measure command: counts distinct non-cli author_tools in scribe/.scribe/updates.jsonl — the healthiest signal is "how many real tools call me" (currently 1: hone). This tick used three MCPs: hone (meta), visionlog (orient), and hone (retain) — first tick where Orient phase actually read visionlog.

Full turn: [`turns/2026-04-21T210717Z.md`](turns/2026-04-21T210717Z.md)
## 2026-04-21T205440Z — improved
First hone run against scribe (not against hone itself). Diagnosed: scribe was blind to its teammates — card-writing callers had to invent teammate names each time, causing naming drift across cards. Changed: added `src/scribe/team.yaml` with 12 team entries (8 MCPs + 4 non-MCP tools: loss-loop, improve-forge, learning-forge, mcp-self-report); added `card.read_team()` loader that fails open; added `scribe_team()` MCP tool that exposes the roster; added pyyaml as a dep; force-included team.yaml in the wheel build. Verified end-to-end: read_team loads 12 entries with correct names. Caught a yaml parse error on the omni entry mid-build (quoted-then-unquoted conflict) and fixed it — first hone tick to catch its own change regressing during Measure. No stepproof integration on scribe yet; will wait until scribe has real usage data to justify stepproof overhead.

Full turn: [`turns/2026-04-21T205440Z.md`](turns/2026-04-21T205440Z.md)
