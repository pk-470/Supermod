"""
Unit tests for ``supermod.features.submissions._utils``. The worksheets are
reached through the lazy ``subs_sheet`` and ``albums_wks`` accessors, bound on
the ``_utils`` module via the ``_constants`` star-import, so patch them there.
"""

from __future__ import annotations

import pytest

from supermod.album_classes import Sub, SubError
from supermod.features.submissions import _utils
from tests.fakes import FakeWorksheet, make_message


@pytest.fixture(autouse=True)
def _restore_accessors():
    """Restore the real lazy accessors after each test (the helpers rebind them)."""
    original = (_utils.subs_sheet, _utils.albums_wks)
    yield
    _utils.subs_sheet, _utils.albums_wks = original


# --- helpers -----------------------------------------------------------------


def _make_sub(
    title="Some Album",
    artist="Some Artist",
    masterlist="voted",
    submitter_id=42,
):
    """Build a Sub directly (bypassing message parsing) for check tests."""
    return Sub(
        artist=artist,
        title=title,
        genres="Pop",
        release_date="2020",
        submitter_name="tester",
        submitter_id=submitter_id,
        masterlist=masterlist,
        message=None,
    )


def _set_subs_sheet(masterlist, rows):
    """Point the ``subs_sheet`` accessor at a parent holding ``masterlist``."""
    parent = FakeWorksheet()
    child = FakeWorksheet(rows)
    parent.add_worksheet(masterlist.upper(), child)
    _utils.subs_sheet = lambda: parent
    return parent, child


def _set_albums_wks(rows):
    """Point the ``albums_wks`` accessor at a FakeWorksheet of discussed albums."""
    ws = FakeWorksheet(rows)
    _utils.albums_wks = lambda: ws
    return ws


# =============================================================================
# submission_make
# =============================================================================


def test_submission_make_well_formed():
    msg = make_message(
        content="Kid A//Radiohead//2000//Electronic//voted",
        author_id=99,
        author_name="alice",
    )
    sub = _utils.submission_make(msg)

    assert isinstance(sub, Sub)
    assert sub.title == "Kid A"
    assert sub.artist == "Radiohead"
    assert sub.release_date == "2000"
    assert "Electronic" in sub.genres
    assert sub.masterlist == "voted"
    assert sub.submitter_name == "alice"
    assert sub.submitter_id == 99
    assert sub.request == "add"


def test_submission_make_replace_sets_request():
    msg = make_message(
        content="replace Old//Band//1999//Rock//new with Kid A//Radiohead//2000//Electronic//new",
    )
    sub = _utils.submission_make(msg)

    assert isinstance(sub, Sub)
    assert sub.request == "replace"
    # Only the part after "with" is parsed.
    assert sub.title == "Kid A"
    assert sub.artist == "Radiohead"
    assert sub.masterlist == "new"


def test_submission_make_malformed_returns_suberror():
    msg = make_message(content="this is not a valid submission")
    sub = _utils.submission_make(msg)

    assert isinstance(sub, SubError)
    assert sub.message is msg


# =============================================================================
# _safe_int
# =============================================================================


def test_safe_int_valid():
    assert _utils._safe_int("123") == 123


def test_safe_int_blank_returns_minus_one():
    assert _utils._safe_int("") == -1


def test_safe_int_non_numeric_returns_minus_one():
    assert _utils._safe_int("abc") == -1


# =============================================================================
# duplicate_check  (tuple-order fix: existing_subs stored as (title, artist))
# =============================================================================


def test_duplicate_check_detects_present_album():
    # Sheet rows used so duplicate_check can read the G-column msg id.
    rows = [
        ["Title", "Artist", "Year", "Genre", "Submitter", "ID", "MsgId"],
        ["Kid A", "Radiohead", "2000", "Electronic", "alice", "99", "55555"],
    ]
    _set_subs_sheet("voted", rows)

    sub = _make_sub(title="Kid A", artist="Radiohead", masterlist="voted")
    # existing_subs stored as (title, artist) — matching sub.title/sub.artist.
    existing = {"voted": [("Kid A", "Radiohead")]}

    found, msg_id = _utils.duplicate_check(sub, existing)
    assert found is True
    assert msg_id == 55555


def test_duplicate_check_absent_album():
    _set_subs_sheet("voted", [["Title", "Artist"]])
    sub = _make_sub(title="OK Computer", artist="Radiohead", masterlist="voted")
    existing = {"voted": [("Kid A", "Radiohead")]}

    found, msg_id = _utils.duplicate_check(sub, existing)
    assert found is False
    assert msg_id == 0


# =============================================================================
# submission_check precedence: discussed > duplicate > user-already
# =============================================================================


def test_submission_check_discussed_wins():
    # Discussed takes precedence even if it is also a duplicate / user repeat.
    _set_subs_sheet(
        "voted",
        [
            ["Title", "Artist", "Year", "Genre", "Submitter", "ID", "MsgId"],
            ["Kid A", "Radiohead", "2000", "Electronic", "alice", "42", "55555"],
        ],
    )
    _set_albums_wks(
        [
            ["Title", "Artist", "Week"],
            ["Kid A", "Radiohead", "7"],
        ]
    )

    sub = _make_sub(title="Kid A", artist="Radiohead", masterlist="voted", submitter_id=42)
    existing = {"voted": [("Kid A", "Radiohead")]}
    submitters = {"voted": [42]}
    discussed = [("Kid A", "Radiohead")]

    result = _utils.submission_check(sub, existing, submitters, discussed)
    assert sub.warning == "discussed"
    assert result == 7


def test_submission_check_duplicate_beats_user_already():
    _set_subs_sheet(
        "voted",
        [
            ["Title", "Artist", "Year", "Genre", "Submitter", "ID", "MsgId"],
            ["Kid A", "Radiohead", "2000", "Electronic", "alice", "42", "55555"],
        ],
    )
    _set_albums_wks([["Title", "Artist", "Week"]])

    sub = _make_sub(title="Kid A", artist="Radiohead", masterlist="voted", submitter_id=42)
    existing = {"voted": [("Kid A", "Radiohead")]}
    submitters = {"voted": [42]}
    discussed = []

    result = _utils.submission_check(sub, existing, submitters, discussed)
    assert sub.warning == "duplicate"
    assert result == 55555


def test_submission_check_user_already():
    _set_subs_sheet(
        "voted",
        [
            ["Title", "Artist", "Year", "Genre", "Submitter", "ID", "MsgId"],
            ["Other Album", "Other Band", "1999", "Rock", "alice", "42", "55555"],
        ],
    )
    _set_albums_wks([["Title", "Artist", "Week"]])

    # Different album, but same submitter already in the masterlist.
    sub = _make_sub(title="Kid A", artist="Radiohead", masterlist="voted", submitter_id=42)
    existing = {"voted": [("Other Album", "Other Band")]}
    submitters = {"voted": [42]}
    discussed = []

    result = _utils.submission_check(sub, existing, submitters, discussed)
    assert sub.warning == "user already in masterlist"
    assert result == 55555


def test_submission_check_clean_returns_zero():
    _set_subs_sheet("voted", [["Title", "Artist"]])
    _set_albums_wks([["Title", "Artist", "Week"]])

    sub = _make_sub(title="Kid A", artist="Radiohead", masterlist="voted", submitter_id=42)
    existing = {"voted": []}
    submitters = {"voted": []}
    discussed = []

    result = _utils.submission_check(sub, existing, submitters, discussed)
    assert sub.warning is None
    assert result == 0


# =============================================================================
# random_album
# =============================================================================


def test_random_album_dedupes_distinct_selection():
    # Header + duplicated rows for one album and one row for another.
    rows = [
        ["Title", "Artist", "Year", "Genre", "Submitter", "ID"],
        ["Kid A", "Radiohead", "2000", "Electronic", "alice", "99"],
        ["Kid A", "Radiohead", "2000", "Electronic", "alice", "99"],
        ["Kid A", "Radiohead", "2000", "Electronic", "alice", "99"],
        ["Loveless", "My Bloody Valentine", "1991", "Shoegaze", "bob", "12"],
    ]
    _set_subs_sheet("voted", rows)

    seen = set()
    for _ in range(50):
        sub = _utils.random_album("voted")
        assert isinstance(sub, Sub)
        seen.add((sub.title, sub.artist))

    # Both distinct albums must be reachable despite the duplicate rows.
    assert ("Kid A", "Radiohead") in seen
    assert ("Loveless", "My Bloody Valentine") in seen
    assert len(seen) == 2


def test_random_album_header_only_returns_none():
    _set_subs_sheet("voted", [["Title", "Artist", "Year", "Genre", "Submitter", "ID"]])
    assert _utils.random_album("voted") is None


def test_random_album_empty_returns_none():
    _set_subs_sheet("voted", [])
    assert _utils.random_album("voted") is None
