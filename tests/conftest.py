"""
Pytest configuration for the Supermod suite. Each feature ``_constants`` module
reads channel/role ids from the environment at import time, so dummy values are
set here before any feature module is imported. Worksheet access is lazy, so no
network call happens on import; tests point the lazy accessors at FakeWorksheets
via the ``set_worksheet`` fixture.
"""

from __future__ import annotations

import os

import pendulum
import pytest

from tests.fakes import FakeWorksheet

# --- dummy environment (must be set before importing any feature module) -----

_DUMMY_ENV = {
    "STAFF_ROLE": "1000",
    "QOTD_CHANNEL": "4001",
    "QOTD_APPROVAL_CHANNEL": "4002",
    "QOTD_SHEET_URL": "https://example.test/qotd",
    "ALBUMS_SHEET_URL": "https://example.test/albums",
    "SUBS_SHEET_URL": "https://example.test/subs",
    "NEWS_SHEET_URL": "https://example.test/news",
    "SUBMISSIONS_CHANNEL": "5002",
    "VOTED_CHANNEL": "5003",
    "NEW_CHANNEL": "5004",
    "MODERN_CHANNEL": "5005",
    "CLASSIC_CHANNEL": "5006",
    "THEME_CHANNEL": "5007",
    "ANYTHING_CHANNEL": "5008",
    "EXPERIMENTAL_ROCK": "2001",
    "HARD_ROCK": "2002",
    "SOFT_ROCK": "2003",
    "PUNK": "2004",
    "CORE": "2005",
    "METAL": "2006",
    "EXTREME_METAL": "2007",
    "CLASSICAL_JAZZ_BLUES": "2008",
    "COUNTRY_FOLK": "2009",
    "ELECTRONIC": "2010",
    "POP_HIP_HOP": "2011",
    "SERVER": "6001",
    "PROMOS_CHANNEL": "6002",
    "ANNOUNCEMENTS_CHANNEL": "7001",
    "TALK_TO_THE_STAFF_CHANNEL": "7004",
    "OL_WEEKLY_PLAYLIST_CHANNEL": "7005",
    "INPUT_RATINGS_HERE_CHANNEL": "7006",
    "FAQS_CHANNEL": "7007",
    "LISTENERS_ROLE": "7008",
}

for _key, _value in _DUMMY_ENV.items():
    os.environ[_key] = _value


# --- fixtures ----------------------------------------------------------------


@pytest.fixture
def frozen_now(monkeypatch):
    """
    Freeze ``pendulum.now`` to a fixed America/Toronto datetime (Wednesday
    2026-06-17 12:00:00) and return it for assertions.
    """
    frozen = pendulum.datetime(2026, 6, 17, 12, 0, 0, tz="America/Toronto")

    def _now(tz=None):
        if tz is not None:
            return frozen.in_timezone(tz)
        return frozen

    monkeypatch.setattr(pendulum, "now", _now)
    return frozen


@pytest.fixture
def set_worksheet(monkeypatch):
    """
    Point a feature module's lazy worksheet accessor (e.g. ``qotd_wks``) at a
    FakeWorksheet. The accessor name is bound on the importing module via the
    ``_constants`` star-import, so patch it there, not on ``_constants``.
    """

    def _set(module, name: str, rows=None) -> FakeWorksheet:
        ws = FakeWorksheet(rows)
        monkeypatch.setattr(module, name, lambda: ws)
        return ws

    return _set
