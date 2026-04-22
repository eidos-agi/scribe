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
