"""Card + updates log I/O for scribe.

All writes are atomic: tmp file + os.replace. Append to updates.jsonl
uses O_APPEND + fsync. Single writer per repo (whoever holds the repo
open), so no locking layer needed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
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


DEFAULT_SCRIBE_YAML = """\
# .scribe/scribe.yaml — which files scribe treats as tracked docs for
# this repo. scribe_review compares each tracked path's last git-touch
# against recent code commits. scribe_suggest (v0.1.2+) ranks which of
# these paths should move for a given code change.
#
# Edit freely: add docs/*, .claude/skills/*.md, anything else that
# tells the project what it is.

version: 0

tracked:
  - .scribe/card.md
  - README.md
  - CHANGELOG.md
"""


def load_config(repo: str) -> dict:
    """Load .scribe/scribe.yaml, or return {} if missing / unparseable.

    Schema (v0):
      tracked: list[str] — repo-relative paths scribe treats as docs
    """
    cfg_path = scribe_dir(repo) / "scribe.yaml"
    if not cfg_path.exists():
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def init(repo: str) -> dict:
    """Create .scribe/ in the target repo. Idempotent. Writes a minimal
    card.md + scribe.yaml if they don't already exist."""
    d = scribe_dir(repo)
    card_path = d / "card.md"
    config_path = d / "scribe.yaml"
    updates_path = d / "updates.jsonl"

    created = False
    if not card_path.exists():
        name = _slug(Path(resolve_repo(repo)).name)
        _atomic_write(
            card_path,
            DEFAULT_CARD_TEMPLATE.format(name=name, now=_now_iso()),
        )
        created = True

    config_created = False
    if not config_path.exists():
        _atomic_write(config_path, DEFAULT_SCRIBE_YAML)
        config_created = True

    _append_jsonl(
        updates_path,
        {
            "timestamp": _now_iso(),
            "action": "init",
            "created_card": created,
            "created_config": config_created,
        },
    )

    return {
        "scribe_dir": str(d),
        "card_path": str(card_path),
        "card_created": created,
        "config_path": str(config_path),
        "config_created": config_created,
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
# v0.1.0+ — scribe_review (ADR-004: coherence pass)
# ---------------------------------------------------------------------

# Default paths scribe treats as tracked docs when no .scribe/scribe.yaml
# is present. A future tick adds the yaml + override.
_DEFAULT_TRACKED_DOCS = (
    ".scribe/card.md",
    "README.md",
    "CHANGELOG.md",
)

# Directories that are NOT "code" for the staleness heuristic. A change
# here doesn't imply docs drifted; these are tooling/state surfaces.
_NON_CODE_PREFIXES = (
    ".scribe/",
    ".hone/",
    ".lighthouse/",
    ".visionlog/",
    ".research/",
    ".ike/",
    ".github/",
    ".claude/",
    "docs/",       # docs themselves; changes here are doc-driven
    "CHANGELOG.md",
    "README.md",
    "LICENSE",
)


def _git_last_touch(repo_root: Path, path: str) -> dict | None:
    """Return {sha, iso, subject} for the most recent commit that
    touched `path`, or None if git has no record. Uses `--follow` so
    renames are handled. Returns None on any subprocess failure —
    scribe must not fail noisily on repos without git history.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1",
             "--follow", "--format=%H|%cI|%s", "--", path],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    sha, iso, subject = out.stdout.strip().split("|", 2)
    return {"sha": sha, "iso": iso, "subject": subject}


def _git_last_code_touch(repo_root: Path) -> dict | None:
    """Find the most recent commit whose changeset touched something
    OTHER than docs / tool state. That commit represents code drift
    docs might need to react to."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "log",
             "--format=%H|%cI|%s", "--name-only", "-n", "50"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None

    commit: dict[str, str] | None = None
    for line in out.stdout.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if "|" in line and line.count("|") >= 2 and len(line.split("|", 2)[0]) == 40:
            sha, iso, subject = line.split("|", 2)
            commit = {"sha": sha, "iso": iso, "subject": subject}
            continue
        # file path under current commit
        if commit is None:
            continue
        if not any(line == p or line.startswith(p) for p in _NON_CODE_PREFIXES):
            return commit
    return None


def review(repo: str, tracked: list[str] | None = None) -> dict:
    """Coherence pass. Returns tracked docs that look stale relative to
    the most recent code commit.

    Heuristic (v0.1.0): a doc is `stale` if the most recent commit that
    touched it predates the most recent non-doc commit. `fresh` otherwise.
    `unknown` when git has no record of the doc (e.g. not committed yet).

    Scribe makes no claim about *what* the doc should say — that's
    `scribe_suggest`'s job (next tick). Review just flags the gap.
    """
    repo_root = resolve_repo(repo)
    if tracked is None:
        # Prefer the repo's own .scribe/scribe.yaml; fall back to defaults.
        cfg = load_config(repo)
        cfg_tracked = cfg.get("tracked") if isinstance(cfg, dict) else None
        if isinstance(cfg_tracked, list) and cfg_tracked:
            tracked = [str(p) for p in cfg_tracked]
        else:
            tracked = list(_DEFAULT_TRACKED_DOCS)

    code_head = _git_last_code_touch(repo_root)

    results: list[dict] = []
    for path in tracked:
        doc_commit = _git_last_touch(repo_root, path)
        if doc_commit is None:
            results.append({
                "path": path,
                "status": "unknown",
                "reason": "not yet committed, or git unavailable",
                "doc_last_touch": None,
                "code_last_touch": code_head,
            })
            continue
        if code_head is None:
            results.append({
                "path": path,
                "status": "fresh",
                "reason": "no subsequent code commits detected",
                "doc_last_touch": doc_commit,
                "code_last_touch": None,
            })
            continue
        if doc_commit["iso"] < code_head["iso"]:
            results.append({
                "path": path,
                "status": "stale",
                "reason": f"last updated at {doc_commit['iso']}; code moved at {code_head['iso']} (commit {code_head['sha'][:7]}: {code_head['subject']!r})",
                "doc_last_touch": doc_commit,
                "code_last_touch": code_head,
            })
        else:
            results.append({
                "path": path,
                "status": "fresh",
                "reason": f"last updated at {doc_commit['iso']}, after code at {code_head['iso']}",
                "doc_last_touch": doc_commit,
                "code_last_touch": code_head,
            })

    stale = [r for r in results if r["status"] == "stale"]
    return {
        "repo": repo,
        "tracked": tracked,
        "stale_count": len(stale),
        "results": results,
    }


# ---------------------------------------------------------------------
# REMOVED: read_team() + team.yaml
# ---------------------------------------------------------------------
# Earlier versions shipped a static team.yaml roster and a read_team()
# loader so the scribe_team() MCP tool could return "who else is in the
# eidos stack." That baked cross-coupling into scribe's library —
# shipping a directory of siblings. Removed per the rule: no enforced
# coupling between tools. If a caller wants a directory of related
# tools, they maintain one in their own environment.
