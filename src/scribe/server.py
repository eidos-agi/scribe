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
def scribe_team() -> dict[str, Any]:
    """Return the roster of tools scribe knows about.

    Useful before writing a new card — callers read the roster,
    pick relevant teammates, and mention them in the card's
    `teammates` field with consistent naming + one-liners.

    Scribe does not enforce this list. It's data, not policy.
    To add a new team member, edit `src/scribe/team.yaml` and
    reinstall (`uv sync`).
    """
    _reload()
    return card.read_team()


@mcp.tool()
def scribe_update(
    repo: str,
    change_summary: str,
    new_card: str | None = None,
    author_tool: str | None = None,
) -> dict[str, Any]:
    """Log a change; optionally overwrite card.md with a fresh synthesis.

    Args:
        repo: path or slug.
        change_summary: one-paragraph description of what changed — goes
            into updates.jsonl as the canonical record of why the card
            moved. Even if new_card is None, the log entry helps.
        new_card: optional full new card contents. If provided, card.md
            is atomically overwritten. Synthesis is the *caller's* job —
            scribe does not run an LLM to compose the new card.
        author_tool: who made the call (e.g., "hone", "stepproof", "cli").
            Stored in the update entry for provenance.

    Returns what was written and where.
    """
    _reload()
    return card.update(
        repo=repo,
        change_summary=change_summary,
        new_card=new_card,
        author_tool=author_tool,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
