"""Card + updates log I/O for scribe.

All writes are atomic: tmp file + os.replace. Append to updates.jsonl
uses O_APPEND + fsync. Single writer per repo (whoever holds the repo
open), so no locking layer needed.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

EIDOS_AGI_ROOT = Path(
    os.environ.get("EIDOS_AGI_ROOT", Path.home() / "repos-eidos-agi")
)


def resolve_repo(repo: str) -> Path:
    """Return an absolute path for a repo argument.

    - absolute path → as-is
    - known sibling slug → ~/repos-eidos-agi/<slug>
    - otherwise → slug resolved under EIDOS_AGI_ROOT (may not exist;
      scribe_init is the one tool allowed to create it)
    """
    p = Path(repo)
    if p.is_absolute():
        return p
    return EIDOS_AGI_ROOT / repo


def scribe_dir(repo: str) -> Path:
    root = resolve_repo(repo)
    d = root / ".scribe"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, default=str).encode() + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line)
        os.fsync(fd)
    finally:
        os.close(fd)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return s or "repo"


DEFAULT_CARD_TEMPLATE = """---
name: {name}
one_liner: (set by scribe_update)
when_to_reach_for: []
invoke: []
capabilities: []
updated: {now}
---

# {name}

This card is scribe-maintained. Tools that modify the repo should call
`mcp__scribe__scribe_update` with a fresh summary so this stays current.

Until then, this is a placeholder. Read the README for the real thing.
"""


def init(repo: str) -> dict:
    """Create .scribe/ in the target repo and write a minimal card if
    none exists. Idempotent."""
    d = scribe_dir(repo)
    card_path = d / "card.md"
    updates_path = d / "updates.jsonl"

    created = False
    if not card_path.exists():
        name = _slug(Path(resolve_repo(repo)).name)
        _atomic_write(
            card_path,
            DEFAULT_CARD_TEMPLATE.format(name=name, now=_now_iso()),
        )
        created = True

    _append_jsonl(
        updates_path,
        {
            "timestamp": _now_iso(),
            "action": "init",
            "created_card": created,
        },
    )

    return {
        "scribe_dir": str(d),
        "card_path": str(card_path),
        "card_created": created,
    }


def read(repo: str, recent: int = 10) -> dict:
    """Return the current card body + last N update-log entries.

    Also returns `callers_seen`: a sorted list of every distinct
    author_tool that has ever called scribe_update for this repo,
    derived from a full scan of updates.jsonl. Useful for repo owners
    to see "who's been updating my card" at a glance. Pure derivation
    from existing data — no new storage.
    """
    d = scribe_dir(repo)
    card_path = d / "card.md"
    updates_path = d / "updates.jsonl"

    card = card_path.read_text(encoding="utf-8") if card_path.exists() else None

    updates: list[dict] = []
    callers: set[str] = set()
    if updates_path.exists():
        all_lines = updates_path.read_text(encoding="utf-8").splitlines()
        # Full scan for callers_seen (authoritative across all history),
        # then slice for recent_updates display.
        for raw in all_lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            author = record.get("author_tool")
            if author:
                callers.add(author)
        for raw in all_lines[-max(1, min(recent, 200)):]:
            raw = raw.strip()
            if not raw:
                continue
            try:
                updates.append(json.loads(raw))
            except json.JSONDecodeError:
                continue

    return {
        "repo": repo,
        "scribe_dir": str(d),
        "card": card,
        "card_exists": card is not None,
        "recent_updates": updates,
        "update_count": _count_lines(updates_path),
        "callers_seen": sorted(callers),
    }


def update(
    repo: str,
    change_summary: str,
    path: str = ".scribe/card.md",
    new_content: str | None = None,
    author_tool: str | None = None,
    # Backward-compat: v0.0.1 callers passed `new_card`. If provided and
    # new_content is None, treat as the v0.0.1 card write.
    new_card: str | None = None,
) -> dict:
    """Log a change. If new_content is provided, overwrite the file at
    `path` atomically. Path is relative to the target repo root.

    v0.1.0 API:
      update(repo, change_summary, path=".scribe/card.md", new_content=...)

    v0.0.1 compat:
      update(repo, change_summary, new_card=...) still works — equivalent
      to update(repo, change_summary, path=".scribe/card.md",
      new_content=new_card).

    ADR-004 — scribe is a technical writer, any file under the repo may
    be a tracked doc. updates.jsonl records `path` on every entry so
    the trajectory of changes across multiple files is queryable.
    """
    repo_root = resolve_repo(repo)
    target_path = repo_root / path
    d = scribe_dir(repo)
    updates_path = d / "updates.jsonl"

    # Unify the two input paths: prefer new_content (v0.1.0), fall back
    # to new_card (v0.0.1 compat).
    content = new_content if new_content is not None else new_card

    file_written = False
    if content is not None:
        _atomic_write(target_path, content)
        file_written = True

    _append_jsonl(
        updates_path,
        {
            "timestamp": _now_iso(),
            "action": "update",
            "path": path,
            "change_summary": change_summary,
            "file_written": file_written,
            # v0.0.1 field, preserved for readers of old logs:
            "card_written": file_written and path == ".scribe/card.md",
            "author_tool": author_tool,
        },
    )

    return {
        "scribe_dir": str(d),
        "path": path,
        "full_path": str(target_path),
        "file_written": file_written,
        # v0.0.1 compat field:
        "card_written": file_written and path == ".scribe/card.md",
        "card_path": str(target_path) if path == ".scribe/card.md" else None,
        "change_logged": True,
    }


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as f:
        return sum(1 for _ in f)


# ---------------------------------------------------------------------
# REMOVED: read_team() + team.yaml
# ---------------------------------------------------------------------
# Earlier versions shipped a static team.yaml roster and a read_team()
# loader so the scribe_team() MCP tool could return "who else is in the
# eidos stack." That baked cross-coupling into scribe's library —
# shipping a directory of siblings. Removed per the rule: no enforced
# coupling between tools. If a caller wants a directory of related
# tools, they maintain one in their own environment.
