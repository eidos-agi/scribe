# Hone notebook — scribe

Accumulated learnings, newest at top.

## 2026-04-21T210717Z — improved
Bridged visionlog → hone.yaml for scribe. Read scribe's three guardrails (GUARD-001 no LLM synthesis, GUARD-002 never cross-repo, GUARD-003 always log) and its vision via visionlog MCP (project_id 7beefb4e), then wrote scribe/.hone/hone.yaml that mirrors them plus two additional hone-level guardrails ("keep scribe small" and "don't break scribe_init/read/update signatures"). Now every hone tick on target=scribe surfaces the visionlog contracts into its ceremony prompt as hard constraints. Also declared the bound instruments (visionlog=true, lighthouse=true) so the ceremony's instruments note correctly tells the agent those MCPs are available. Measure command: counts distinct non-cli author_tools in scribe/.scribe/updates.jsonl — the healthiest signal is "how many real tools call me" (currently 1: hone). This tick used three MCPs: hone (meta), visionlog (orient), and hone (retain) — first tick where Orient phase actually read visionlog.

Full turn: [`turns/2026-04-21T210717Z.md`](turns/2026-04-21T210717Z.md)
## 2026-04-21T205440Z — improved
First hone run against scribe (not against hone itself). Diagnosed: scribe was blind to its teammates — card-writing callers had to invent teammate names each time, causing naming drift across cards. Changed: added `src/scribe/team.yaml` with 12 team entries (8 MCPs + 4 non-MCP tools: loss-loop, improve-forge, learning-forge, mcp-self-report); added `card.read_team()` loader that fails open; added `scribe_team()` MCP tool that exposes the roster; added pyyaml as a dep; force-included team.yaml in the wheel build. Verified end-to-end: read_team loads 12 entries with correct names. Caught a yaml parse error on the omni entry mid-build (quoted-then-unquoted conflict) and fixed it — first hone tick to catch its own change regressing during Measure. No stepproof integration on scribe yet; will wait until scribe has real usage data to justify stepproof overhead.

Full turn: [`turns/2026-04-21T205440Z.md`](turns/2026-04-21T205440Z.md)
