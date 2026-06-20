"""
Pytest configuration for the Supermod suite. Feature ``_constants`` modules run
``gspread.open_by_url(...)`` at import time, so this module injects fake
``supermod.features.<feat>._constants`` modules into ``sys.modules`` before any
feature code is imported, letting later imports resolve the fakes instead of
hitting Google."""

from __future__ import annotations

import sys
import types

import pendulum
import pytest

from tests.fakes import FakeWorksheet  # noqa: E402


def _make_constants_module(name: str, attrs: dict) -> None:
    """Register a fake ``supermod.features.<feat>._constants`` module."""
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


# --- dummy ids / values used across features ---------------------------------

STAFF_ROLE = 1000

_GENRE_CHANNELS = {
    "Experimental Rock": 2001,
    "Hard Rock": 2002,
    "Soft Rock": 2003,
    "Punk": 2004,
    "Core": 2005,
    "Metal": 2006,
    "Extreme Metal": 2007,
    "Classical / Jazz / Blues": 2008,
    "Country / Folk": 2009,
    "Electronic": 2010,
    "Pop / Hip Hop": 2011,
}

_MASTERLIST_CHANNEL_DICT = {
    "voted": 3001,
    "new": 3002,
    "modern": 3003,
    "classic": 3004,
    "theme": 3005,
    "anything": 3006,
}


# --- register the fake _constants modules (must run at conftest import) ------

_make_constants_module(
    "supermod.features.general._constants",
    {"STAFF_ROLE": STAFF_ROLE},
)

_make_constants_module(
    "supermod.features.qotd._constants",
    {
        "QOTD_WKS": FakeWorksheet(),
        "QOTD_CHANNEL": 4001,
        "QOTD_APPROVAL_CHANNEL": 4002,
        "QOTD_HOUR": 6,
        "QOTD_MINUTE": 0,
        "STAFF_ROLE": STAFF_ROLE,
    },
)

_make_constants_module(
    "supermod.features.submissions._constants",
    {
        "ALBUMS_WKS": FakeWorksheet(),
        "SUBS_SHEET": FakeWorksheet(),
        "SUB_APPROVAL_CHANNEL": 5001,
        "SUBMISSIONS_CHANNEL": 5002,
        "VOTED_CHANNEL": 5003,
        "NEW_CHANNEL": 5004,
        "MODERN_CHANNEL": 5005,
        "CLASSIC_CHANNEL": 5006,
        "THEME_CHANNEL": 5007,
        "ANYTHING_CHANNEL": 5008,
        "MASTERLIST_CHANNEL_DICT": dict(_MASTERLIST_CHANNEL_DICT),
        "STAFF_ROLE": STAFF_ROLE,
    },
)

_make_constants_module(
    "supermod.features.newsletter._constants",
    {
        "NEWS_SHEET": FakeWorksheet(),
        "GENRE_CHANNELS": dict(_GENRE_CHANNELS),
        "STAFF_ROLE": STAFF_ROLE,
    },
)

_make_constants_module(
    "supermod.features.promotions._constants",
    {
        "PROMOS_WKS": FakeWorksheet(),
        "SERVER": 6001,
        "PROMOS_CHANNEL": 6002,
        "REJECTED_PROMOS_CHANNEL": 6003,
        "STAFF_ROLE": STAFF_ROLE,
    },
)

_make_constants_module(
    "supermod.features.submissions_status._constants",
    {
        "ANNOUNCEMENTS_CHANNEL": 7001,
        "SUBMISSIONS_CHANNEL": 7002,
        "VOTED_CHANNEL": 7003,
        "TALK_TO_THE_STAFF_CHANNEL": 7004,
        "OL_WEEKLY_PLAYLIST_CHANNEL": 7005,
        "INPUT_RATINGS_HERE_CHANNEL": 7006,
        "FAQS_CHANNEL": 7007,
        "LISTENERS_ROLE_MENTION": "<@&7008>",
        "SUBMISSIONS_OPEN_DAY": "Sunday",
        "SUBMISSIONS_OPEN_HOUR": 0,
        "SUBMISSIONS_OPEN_MINUTE": 0,
        "SUBMISSIONS_CLOSED_DAY": "Thursday",
        "SUBMISSIONS_CLOSED_HOUR": 0,
        "SUBMISSIONS_CLOSED_MINUTE": 0,
    },
)


# --- fixtures ----------------------------------------------------------------


@pytest.fixture
def frozen_now(monkeypatch):
    """
    Freeze ``pendulum.now`` to a fixed America/Toronto datetime (Wednesday
    2026-06-17 12:00:00) and return it for assertions."""
    frozen = pendulum.datetime(2026, 6, 17, 12, 0, 0, tz="America/Toronto")

    def _now(tz=None):
        if tz is not None:
            return frozen.in_timezone(tz)
        return frozen

    monkeypatch.setattr(pendulum, "now", _now)
    return frozen


@pytest.fixture
def set_worksheet():
    """
    Point a feature module's worksheet name at a FakeWorksheet. The name lives
    on the importing ``_utils``/cog module, so patch it there, not on
    ``_constants``."""

    def _set(module, name: str, rows=None) -> FakeWorksheet:
        ws = FakeWorksheet(rows)
        setattr(module, name, ws)
        return ws

    return _set
