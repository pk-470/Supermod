"""
Tests for supermod.features.qotd._utils. Worksheet columns are A: id,
B: repeatable ("Y"/"N"), C: question text, D: used count. ``_utils`` binds
``QOTD_WKS`` on its own module, so point it at a FakeWorksheet via the
``set_worksheet`` fixture."""

from __future__ import annotations

import pytest

from supermod.features.qotd import _utils

HEADER = ["ID", "Repeatable", "Question", "Used"]


# --- qotd_get ---------------------------------------------------------------


def test_qotd_get_excludes_header_and_used_includes_eligible(monkeypatch, set_worksheet):
    rows = [
        HEADER,
        ["1", "N", "Unused non-repeatable", ""],   # eligible
        ["2", "N", "Used non-repeatable", "1"],     # excluded (used)
        ["3", "Y", "Used repeatable", "5"],         # eligible (repeatable)
        ["4", "Y", "Unused repeatable", ""],        # eligible
    ]
    set_worksheet(_utils, "QOTD_WKS", rows)

    # Make random.choice deterministic so we can inspect the pool it was given.
    captured: dict = {}

    def fake_choice(pool):
        captured["pool"] = pool
        return pool[0]

    monkeypatch.setattr(_utils.random, "choice", fake_choice)

    result = _utils.qotd_get()
    pool = captured["pool"]
    texts = {row[2] for row in pool}

    # Header excluded (B is neither "Y" nor "N").
    assert HEADER not in pool
    assert "Question" not in texts
    # Used non-repeatable excluded.
    assert "Used non-repeatable" not in texts
    # Everything eligible is present.
    assert texts == {
        "Unused non-repeatable",
        "Used repeatable",
        "Unused repeatable",
    }
    assert result in pool


def test_qotd_get_returns_none_when_pool_empty(monkeypatch, set_worksheet):
    # Header + only ineligible rows -> filtered pool is empty -> None (the fix).
    rows = [
        HEADER,
        ["1", "N", "Used non-repeatable", "3"],   # excluded (used)
        ["2", "N", "", ""],                        # excluded (no text)
    ]
    set_worksheet(_utils, "QOTD_WKS", rows)

    # Guard: random.choice must never be called on an empty pool.
    def boom(_pool):
        raise AssertionError("random.choice should not run when pool is empty")

    monkeypatch.setattr(_utils.random, "choice", boom)

    assert _utils.qotd_get() is None


def test_qotd_get_returns_none_when_sheet_empty(set_worksheet):
    set_worksheet(_utils, "QOTD_WKS", [])
    assert _utils.qotd_get() is None


# --- mark_as_used -----------------------------------------------------------


def test_mark_as_used_increments_count_of_matched_row(set_worksheet):
    rows = [
        HEADER,
        ["1", "N", "First question", ""],
        ["2", "N", "Second question", "2"],
    ]
    ws = set_worksheet(_utils, "QOTD_WKS", rows)

    # Empty count starts at 0 -> 1.
    _utils.mark_as_used(["1", "N", "First question", ""])
    assert ws.rows[1][3] == 1

    # Existing count 2 -> 3, and other rows untouched.
    _utils.mark_as_used(["2", "N", "Second question", "2"])
    assert ws.rows[2][3] == 3
    assert ws.rows[1][3] == 1


@pytest.mark.xfail(reason="Group C #6: mark_as_used finds by text, marks the wrong (first) row on duplicates")
def test_mark_as_used_marks_correct_row_with_duplicate_text(set_worksheet):
    # Two rows share identical question text. The caller passes the *second*
    # one (already used once), so its count should go 1 -> 2 while the first
    # stays untouched. find() matches the first occurrence, so the wrong row
    # is incremented -> this documents the gap.
    rows = [
        HEADER,
        ["1", "Y", "Duplicate question", ""],     # first occurrence, unused
        ["2", "Y", "Duplicate question", "1"],     # the one actually used
    ]
    ws = set_worksheet(_utils, "QOTD_WKS", rows)

    _utils.mark_as_used(["2", "Y", "Duplicate question", "1"])

    assert ws.rows[2][3] == 2   # the intended (second) row incremented
    assert ws.rows[1][3] == ""  # first occurrence left untouched
