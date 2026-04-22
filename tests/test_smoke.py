"""Smoke tests for scribe.

Covers card.py — scribe's only behavior module. Uses absolute repo
paths pointing at tmp_path so EIDOS_AGI_ROOT resolution is bypassed
and tests never touch real repos.
"""

from __future__ import annotations


# ---------------------------------------------------------------------
# init + read + update roundtrip
# ---------------------------------------------------------------------


def test_init_creates_scribe_dir(tmp_path):
    from scribe import card

    repo = str(tmp_path / "myrepo")
    r = card.init(repo)

    assert (tmp_path / "myrepo" / ".scribe").exists()
    assert (tmp_path / "myrepo" / ".scribe" / "card.md").exists()
    assert r["card_created"] is True


def test_init_is_idempotent(tmp_path):
    from scribe import card

    repo = str(tmp_path / "myrepo")
    card.init(repo)
    r2 = card.init(repo)

    assert r2["card_created"] is False


def test_read_returns_card_and_updates(tmp_path):
    from scribe import card

    repo = str(tmp_path / "r")
    card.init(repo)
    card.update(repo, change_summary="first real change", author_tool="hone")

    data = card.read(repo, recent=10)
    assert data["card_exists"] is True
    assert data["card"] is not None
    assert data["update_count"] >= 2  # init + update


def test_update_log_only_when_no_new_card(tmp_path):
    """GUARD-003 regression: every update must be logged even without new_card."""
    from scribe import card

    repo = str(tmp_path / "r")
    card.init(repo)
    before = card.read(repo)["update_count"]

    r = card.update(repo, change_summary="log-only tick", author_tool="test")

    assert r["card_written"] is False
    assert r["change_logged"] is True
    assert card.read(repo)["update_count"] == before + 1


def test_callers_seen_aggregates_distinct_author_tools(tmp_path):
    """TASK-0003: scribe_read returns a sorted list of distinct author_tools
    seen across all updates.jsonl entries."""
    from scribe import card

    repo = str(tmp_path / "r")
    card.init(repo)  # author_tool not set on init entry
    card.update(repo, change_summary="first", author_tool="hone")
    card.update(repo, change_summary="second", author_tool="hone")
    card.update(repo, change_summary="third", author_tool="stepproof")
    card.update(repo, change_summary="fourth", author_tool="cli")

    data = card.read(repo, recent=2)
    assert data["callers_seen"] == ["cli", "hone", "stepproof"]


def test_callers_seen_empty_when_no_updates(tmp_path):
    from scribe import card

    repo = str(tmp_path / "r")
    # Don't even init — no updates.jsonl
    d = card.scribe_dir(repo)
    (d / "updates.jsonl").write_text("")

    data = card.read(repo)
    assert data["callers_seen"] == []


def test_update_writes_card_when_new_card_provided(tmp_path):
    from scribe import card

    repo = str(tmp_path / "r")
    card.init(repo)

    r = card.update(
        repo=repo,
        change_summary="replacing card",
        new_card="---\nname: newcard\n---\n# replaced",
        author_tool="test",
    )

    assert r["card_written"] is True
    assert "replaced" in card.read(repo)["card"]


# ---------------------------------------------------------------------
# v0.1.0 — path-generic API (ADR-004)
# ---------------------------------------------------------------------


def test_update_writes_arbitrary_path(tmp_path):
    """ADR-004: scribe_update can write any file under the repo, not
    just .scribe/card.md."""
    from scribe import card

    repo = str(tmp_path / "r")
    card.init(repo)

    r = card.update(
        repo=repo,
        path="README.md",
        change_summary="refresh README data-layer section",
        new_content="# Repo\n\nThree tables: users, sessions, user_preferences.\n",
        author_tool="scribe-review",
    )

    assert r["file_written"] is True
    assert r["path"] == "README.md"
    assert (tmp_path / "r" / "README.md").read_text() == "# Repo\n\nThree tables: users, sessions, user_preferences.\n"
    # The card was NOT written — this was a different file.
    assert r["card_written"] is False


def test_update_logs_path_on_every_entry(tmp_path):
    """ADR-004 + GUARD-003: updates.jsonl records `path` so the
    trajectory of changes across multiple files is queryable."""
    from scribe import card
    import json
    from pathlib import Path

    repo = str(tmp_path / "r")
    card.init(repo)
    card.update(repo, path="README.md", change_summary="x", new_content="A", author_tool="t")
    card.update(repo, path="CHANGELOG.md", change_summary="y", new_content="B", author_tool="t")
    card.update(repo, path="docs/schema.md", change_summary="z", new_content="C", author_tool="t")

    updates_path = Path(tmp_path / "r" / ".scribe" / "updates.jsonl")
    entries = [json.loads(line) for line in updates_path.read_text().splitlines() if line.strip()]

    # init + 3 updates
    paths_seen = [e.get("path") for e in entries if e.get("action") == "update"]
    assert paths_seen == ["README.md", "CHANGELOG.md", "docs/schema.md"]


def test_v0_0_1_new_card_still_works(tmp_path):
    """Backward compat: v0.0.1 callers passing `new_card=` still work."""
    from scribe import card

    repo = str(tmp_path / "r")
    card.init(repo)

    r = card.update(
        repo=repo,
        change_summary="v0.0.1 style call",
        new_card="---\nname: legacy\n---\n",
        author_tool="legacy-caller",
    )

    # Writes to default .scribe/card.md
    assert r["card_written"] is True
    assert r["path"] == ".scribe/card.md"


# ---------------------------------------------------------------------
# ADR-001 regression — no LLM synthesis inside scribe
# ---------------------------------------------------------------------


def test_no_llm_sdk_imports_in_source():
    """GUARD-001 / ADR-001: scribe must not import LLM SDKs."""
    from pathlib import Path

    src_dir = Path(__file__).resolve().parent.parent / "src" / "scribe"
    banned = {"anthropic", "openai", "langchain", "litellm"}

    for py in src_dir.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for name in banned:
            # Match `import X` or `from X` at line starts
            assert f"\nimport {name}" not in text, (
                f"{py.name}: GUARD-001 violated — imports {name}"
            )
            assert f"\nfrom {name}" not in text, (
                f"{py.name}: GUARD-001 violated — imports from {name}"
            )
