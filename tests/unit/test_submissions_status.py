"""
Tests for the weekly submissions status announcements: the Sunday "submissions
open" and Thursday "submissions closed" posts, both pinging the Listeners role.
Each test runs one tick of the loop body at a frozen America/Toronto time.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pendulum
import pytest

from supermod.features.submissions_status import submissions_status as status_mod

LISTENERS = "<@&7008>"


@pytest.fixture
def announcements(monkeypatch):
    """The announcements channel double; every other channel id resolves to None."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    monkeypatch.setattr(status_mod, "is_local", lambda: True)
    return channel


async def tick(monkeypatch, channel, when: str, resolves: bool = True) -> None:
    """Run the loop body once at ``when`` (America/Toronto)."""
    now = pendulum.parse(when, tz="America/Toronto")
    monkeypatch.setattr(pendulum, "now", lambda tz=None: now)
    bot = MagicMock()
    bot.get_channel.side_effect = lambda channel_id: (
        channel if resolves and channel_id == status_mod.ANNOUNCEMENTS_CHANNEL else None
    )
    cog = status_mod.SubmissionsStatus(bot)
    await status_mod.SubmissionsStatus.submissions_status.coro(cog)


def sent(channel) -> tuple[str, discord.AllowedMentions]:
    channel.send.assert_awaited_once()
    call = channel.send.await_args
    return call.args[0], call.kwargs["allowed_mentions"]


def assert_pings_only_listeners(allowed: discord.AllowedMentions) -> None:
    payload = allowed.to_dict()
    assert payload["parse"] == []  # no @everyone, no other users or roles
    assert payload["roles"] == [7008]


async def test_sunday_midnight_posts_submissions_open(monkeypatch, announcements):
    await tick(monkeypatch, announcements, "2026-10-04T00:00:30")  # a Sunday

    text, allowed = sent(announcements)
    assert text.startswith(f"Hello {LISTENERS}! Voting has closed")
    # The linked channels are mentioned by id, so they render whatever their type.
    for channel_id in (
        status_mod.OL_WEEKLY_PLAYLIST_CHANNEL,
        status_mod.INPUT_RATINGS_HERE_CHANNEL,
        status_mod.FAQS_CHANNEL,
        status_mod.TALK_TO_THE_STAFF_CHANNEL,
    ):
        assert f"<#{channel_id}>" in text
    assert_pings_only_listeners(allowed)


async def test_thursday_midnight_posts_submissions_closed(monkeypatch, announcements):
    await tick(monkeypatch, announcements, "2026-10-08T00:00:30")  # a Thursday

    text, allowed = sent(announcements)
    assert text.startswith(f"Hello {LISTENERS}! <#{status_mod.SUBMISSIONS_CHANNEL}>")
    assert f"<#{status_mod.VOTED_CHANNEL}>" in text
    assert "vote up to 5 albums" in text
    assert_pings_only_listeners(allowed)


@pytest.mark.parametrize(
    "when",
    [
        "2026-10-04T00:01:00",  # Sunday, one minute late
        "2026-10-03T23:59:00",  # Saturday, one minute early
        "2026-10-05T00:00:00",  # Monday midnight
        "2026-10-08T12:00:00",  # Thursday noon
    ],
)
async def test_no_announcement_outside_the_scheduled_minutes(
    monkeypatch, announcements, when
):
    await tick(monkeypatch, announcements, when)

    announcements.send.assert_not_awaited()


async def test_missing_announcements_channel_skips_without_crashing(
    monkeypatch, announcements, caplog
):
    await tick(monkeypatch, announcements, "2026-10-04T00:00:30", resolves=False)

    announcements.send.assert_not_awaited()
    assert "was not posted" in caplog.text
