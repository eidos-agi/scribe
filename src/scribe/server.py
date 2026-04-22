"""Scribe MCP server.

Three tools:

  - scribe_init(repo)                                         — create .scribe/
  - scribe_read(repo, recent?=10)                             — read card + updates
  - scribe_update(repo, change_summary, new_card?, author?)   — log a change

Scribe is data-layer only. No LLM synthesis inside scribe. The calling
tool (hone, stepproof, lighthouse, or a human at the keyboard) holds
the session context, so the calling tool generates the fresh card and
hands it to scribe_update. Scribe's job is *only* to store + log.
"""

from __future__ import annotations

import importlib
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import card

mcp = FastMCP("scribe")


def _reload() -> None:
    """Re-import card so on-disk changes propagate without a restart.

    Same pattern hone uses. Tool functions are captured by FastMCP at
    registration time and can't be hot-reloaded, but they use
    module-attribute access (card.init, card.read, card.update) which
    resolves at call-time against the reloaded module.
    """
    importlib.reload(card)


@mcp.tool()
def scribe_init(repo: str) -> dict[str, Any]:
    """Create .scribe/ in the target repo with a minimal card if none exists.

    Args:
        repo: absolute path, or a known eidos-agi sibling slug ("hone",
            "stepproof", ...), or an arbitrary slug resolved under
            ~/repos-eidos-agi/.

    Idempotent — safe to call many times.
    """
    _reload()
    return card.init(repo)


@mcp.tool()
def scribe_read(repo: str, recent: int = 10) -> dict[str, Any]:
    """Return the current card + the last N entries from updates.jsonl."""
    _reload()
    return card.read(repo, recent=recent)


@mcp.tool()
def scribe_update(
    repo: str,
    change_summary: str,
    path: str = ".scribe/card.md",
    new_content: str | None = None,
    author_tool: str | None = None,
    new_card: str | None = None,
) -> dict[str, Any]:
    """Log a change; optionally overwrite the file at `path` atomically.

    v0.1.0 API — path is now explicit. Scribe can update any tracked doc
    in the repo: card.md, README.md, CHANGELOG.md, docs/*, .claude/skills/*.md,
    etc. See visionlog ADR-004 for the reframe from data-layer-only to
    technical-writer.

    Args:
        repo: path or slug.
        change_summary: one-paragraph description of what changed. Goes
            into updates.jsonl as the canonical record of why the write
            happened. Required regardless of whether content is written.
        path: repo-relative destination. Defaults to ".scribe/card.md"
            (the v0.0.1 behavior) so existing v0.0.1 callers still work.
        new_content: optional. If provided, the file at `path` is
            atomically overwritten with this content. Synthesis is the
            caller's job — scribe does not import an LLM SDK. For
            agent-synthesized updates, the caller runs claude -p or
            similar and hands the result in here.
        author_tool: who made the call (e.g., "hone", "stepproof", "cli").
            Stored in the update entry for provenance.
        new_card: v0.0.1 backward-compat alias for new_content when
            path is the default card. Kept so old callers keep working.
    """
    _reload()
    return card.update(
        repo=repo,
        change_summary=change_summary,
        path=path,
        new_content=new_content,
        author_tool=author_tool,
        new_card=new_card,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
