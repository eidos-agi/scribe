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
    """Return the current card body + last N update-log entries."""
    d = scribe_dir(repo)
    card_path = d / "card.md"
    updates_path = d / "updates.jsonl"

    card = card_path.read_text(encoding="utf-8") if card_path.exists() else None

    updates: list[dict] = []
    if updates_path.exists():
        lines = updates_path.read_text(encoding="utf-8").splitlines()
        for raw in lines[-max(1, min(recent, 200)):]:
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
    }


def update(
    repo: str,
    change_summary: str,
    new_card: str | None = None,
    author_tool: str | None = None,
) -> dict:
    """Log a change. If new_card is provided, overwrite card.md atomically."""
    d = scribe_dir(repo)
    card_path = d / "card.md"
    updates_path = d / "updates.jsonl"

    card_written = False
    if new_card is not None:
        _atomic_write(card_path, new_card)
        card_written = True

    _append_jsonl(
        updates_path,
        {
            "timestamp": _now_iso(),
            "action": "update",
            "change_summary": change_summary,
            "card_written": card_written,
            "author_tool": author_tool,
        },
    )

    return {
        "scribe_dir": str(d),
        "card_path": str(card_path),
        "card_written": card_written,
        "change_logged": True,
    }


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as f:
        return sum(1 for _ in f)


def read_team() -> dict:
    """Load the known-team roster shipped with scribe.

    The roster is a static yaml at src/scribe/team.yaml. Edit it when
    the stack grows. This is NOT cross-repo aggregation (GUARD-002) —
    it's a static roster of tools scribe knows about, so card-writing
    callers can reach for teammates by name with consistent wording.

    Fails open: if PyYAML isn't installed or the file is missing,
    return an empty team with an explanatory note.
    """
    team_path = Path(__file__).parent / "team.yaml"
    if not team_path.exists():
        return {"version": 0, "team": [], "note": "team.yaml missing"}
    try:
        import yaml  # type: ignore
    except ImportError:
        return {
            "version": 0,
            "team": [],
            "note": "PyYAML not installed; install scribe with `uv sync`",
        }
    try:
        data = yaml.safe_load(team_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"version": 0, "team": [], "note": f"parse error: {e}"}
    if not isinstance(data, dict):
        return {"version": 0, "team": [], "note": "team.yaml not a mapping"}
    return data
