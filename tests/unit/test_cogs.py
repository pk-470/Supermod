"""
Cog-level tests for command and loop behaviour that sits outside the pure
``_utils`` modules. Command bodies are run directly via ``invoke`` (which skips
the staff check), loops are kept from starting by patching ``is_local``,
and Discord channels are ``MagicMock(spec=...)`` so ``isinstance`` checks pass.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from supermod.album_classes import Sub
from supermod.features.general import general as general_mod
from supermod.features.promotions import promotions as promotions_mod
from supermod.features.qotd import qotd as qotd_mod
from supermod.features.submissions import submissions as submissions_mod
from tests.fakes import FakeWorksheet, make_ctx, make_message

SUBS_HEADER = [
    "Title",
    "Artist",
    "Year",
    "Genre",
    "Submitter Name",
    "Submitter ID",
    "Message ID",
]


async def invoke(command: Any, cog, ctx) -> None:
    """Run a command's body for ``cog`` without a bot or its checks."""
    await command.callback(cog, ctx)


def _text_channel(messages=()):
    """A TextChannel double whose history() yields ``messages``."""
    channel = MagicMock(spec=discord.TextChannel)

    async def history(*args, **kwargs):
        for msg in messages:
            yield msg

    channel.history = history
    return channel


def _submissions_cog(monkeypatch, channel):
    monkeypatch.setattr(submissions_mod, "is_local", lambda: True)
    bot = MagicMock()
    bot.get_channel.return_value = channel
    bot.get_user.return_value = None  # not cached, so fetch_user is used
    bot.fetch_user = AsyncMock(return_value=MagicMock(display_name="Submitter"))
    return submissions_mod.Submissions(bot)


# --- ,archive ----------------------------------------------------------------


@pytest.mark.parametrize(
    "channel_type", [discord.TextChannel, discord.Thread, discord.VoiceChannel]
)
async def test_archive_exports_any_channel_with_history(monkeypatch, channel_type):
    export = AsyncMock(return_value="<html></html>")
    monkeypatch.setattr(general_mod.chat_exporter, "export", export)
    ctx = make_ctx()
    ctx.channel = MagicMock(spec=channel_type)
    ctx.channel.name = "some-channel"

    await invoke(general_mod.General.archive, general_mod.General(MagicMock()), ctx)

    export.assert_awaited_once()
    assert isinstance(ctx.sent[-1]["file"], discord.File)


async def test_archive_rejects_channels_without_history():
    ctx = make_ctx()
    ctx.channel = MagicMock(spec=discord.CategoryChannel)

    await invoke(general_mod.General.archive, general_mod.General(MagicMock()), ctx)

    assert ctx.sent == ["Please specify a valid channel id."]


# --- ,qotd_reset ---------------------------------------------------------------


async def test_qotd_reset_zeroes_questions_in_one_write(monkeypatch, set_worksheet):
    monkeypatch.setattr(qotd_mod, "is_local", lambda: True)
    rows = [
        ["", "Repeatable", "Message", ""],
        ["Question", "N", "First", "3"],
        ["", "", "", "note"],  # no question text: left alone
        ["Question", "N", "Second"],  # short row (blank count)
    ]
    ws = set_worksheet(qotd_mod, "qotd_wks", rows)
    ctx = make_ctx()

    await invoke(qotd_mod.QOTD.qotd_reset, qotd_mod.QOTD(MagicMock()), ctx)

    assert ws.write_count == 1
    assert [row[3] for row in ws.rows[1:]] == [0, "note", 0]
    assert ctx.sent == ["Number of uses for all questions set to 0."]


# --- promotions loop --------------------------------------------------------------


def test_promos_loop_runs_at_the_top_of_every_hour():
    times = promotions_mod.Promotions.promos_loop.time
    assert times is not None
    assert len(times) == 24
    assert {(t.minute, t.second) for t in times} == {(0, 0)}


async def test_read_promos_retries_through_transient_errors(monkeypatch):
    monkeypatch.setattr(promotions_mod, "is_local", lambda: True)
    monkeypatch.setattr(promotions_mod, "PROMO_READ_RETRY_SECONDS", 0)
    ws = FakeWorksheet([["header"], ["promo"]])
    calls = iter([RuntimeError("503"), ws])

    def flaky():
        result = next(calls)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(promotions_mod, "promos_wks", flaky)
    cog = promotions_mod.Promotions(MagicMock())

    assert await cog._read_promos() == [["promo"]]


async def test_read_promos_gives_up_after_all_attempts(monkeypatch):
    monkeypatch.setattr(promotions_mod, "is_local", lambda: True)
    monkeypatch.setattr(promotions_mod, "PROMO_READ_RETRY_SECONDS", 0)
    attempts = []

    def down():
        attempts.append(1)
        raise RuntimeError("503")

    monkeypatch.setattr(promotions_mod, "promos_wks", down)
    cog = promotions_mod.Promotions(MagicMock())

    assert await cog._read_promos() is None
    assert len(attempts) == promotions_mod.PROMO_READ_ATTEMPTS


# --- submissions ----------------------------------------------------------------


async def test_update_subs_sheet_writes_once_and_clears_leftovers(
    monkeypatch, set_worksheet
):
    good = make_message("Album _by_ Band (2020) (Rock) <@!42>")
    good.id = 777
    bad = make_message("not a masterlist post")
    bad.jump_url = "https://discord.com/channels/0/0/bad"
    cog = _submissions_cog(monkeypatch, _text_channel([good, bad]))
    stale = ["Old", "Row", "1999", "Pop", "x", "1", "2"]
    ws = set_worksheet(submissions_mod, "subs_sheet", [SUBS_HEADER] + [stale] * 3)
    ctx = make_ctx()

    await cog._update_subs_sheet(ctx, "new")

    assert ws.rows == [
        SUBS_HEADER,
        ["Album", "Band", "2020", "Rock", "Submitter", "42", "777"],
    ]
    assert ws.write_count == 2  # one write plus one clear of the old rows
    assert "https://discord.com/channels/0/0/bad" in ctx.sent


async def test_update_subs_sheet_uses_cached_users_without_fetching(
    monkeypatch, set_worksheet
):
    post = make_message("Album _by_ Band (2020) (Rock) <@!42>")
    cog = _submissions_cog(monkeypatch, _text_channel([post]))
    bot: Any = cog.bot
    bot.get_user.return_value = MagicMock(display_name="Cached")
    ws = set_worksheet(submissions_mod, "subs_sheet", [SUBS_HEADER])

    await cog._update_subs_sheet(make_ctx(), "new")

    assert ws.rows[1][4] == "Cached"
    bot.fetch_user.assert_not_awaited()


async def test_update_subs_sheet_leaves_sheet_intact_when_write_fails(
    monkeypatch, set_worksheet
):
    cog = _submissions_cog(monkeypatch, _text_channel([]))
    old = [SUBS_HEADER, ["Old", "Row", "1999", "Pop", "x", "1", "2"]]
    ws = set_worksheet(submissions_mod, "subs_sheet", old)
    monkeypatch.setattr(ws, "update", MagicMock(side_effect=RuntimeError("502")))

    with pytest.raises(RuntimeError):
        await cog._update_subs_sheet(make_ctx(), "new")

    assert ws.rows == old


async def test_replace_with_already_deleted_post_still_submits(
    monkeypatch, set_worksheet
):
    channel = _text_channel()
    channel.fetch_message = AsyncMock(
        side_effect=discord.NotFound(MagicMock(status=404), "Unknown Message")
    )
    channel.send = AsyncMock(return_value=MagicMock(id=555))
    cog = _submissions_cog(monkeypatch, channel)
    ws = set_worksheet(
        submissions_mod,
        "subs_sheet",
        [SUBS_HEADER, ["Old", "Album", "2019", "Rock", "Fan", "42", "999"]],
    )
    message = make_message(author_id=42)
    message.add_reaction = AsyncMock()
    sub = Sub(
        artist="Band",
        title="New",
        genres="Rock",
        release_date="2020",
        submitter_name="Fan",
        submitter_id=42,
        masterlist="new",
        message=message,
        request="replace",
    )

    await cog._submit_album(sub)

    assert ws.rows == [
        SUBS_HEADER,
        ["New", "Band", "2020", "Rock", "Fan", "42", "555"],
    ]
    message.add_reaction.assert_awaited_once_with("🆗")


# --- masterlist post format <-> parser -----------------------------------------


@pytest.mark.parametrize(
    ("title", "artist", "year", "genres"),
    [
        ("Album", "Band", "2020", "Rock"),
        ("Live (Deluxe Edition)", "Band", "2020", "Rock"),
        ("Album", "Nirvana (UK)", "1992", "Rock"),
        ("Album", "Band", "2020", "Death Metal, Black Metal"),
        ("A/B", "The Band", "1975", "Pop"),
    ],
)
async def test_masterlist_post_parses_back_to_the_same_submission(
    monkeypatch, title, artist, year, genres
):
    # The sheet rebuild reads masterlist posts back, so every post the bot
    # writes must parse back into the same submission.
    cog = _submissions_cog(monkeypatch, _text_channel())
    sub = Sub(
        artist=artist,
        title=title,
        genres=genres,
        release_date=year,
        submitter_name="Submitter",
        submitter_id=42,
        masterlist="new",
    )

    back = await cog._masterlist_sub_make(sub.masterlist_format(), "new")

    assert (back.title, back.artist, back.release_date, back.genres) == (
        sub.title,
        sub.artist,
        sub.release_date,
        sub.genres,
    )
    assert back.submitter_id == 42
    assert back.submitter_name == "Submitter"


async def test_masterlist_parser_accepts_plain_user_mentions(monkeypatch):
    cog = _submissions_cog(monkeypatch, _text_channel())
    back = await cog._masterlist_sub_make("Album _by_ Band (2020) (Rock) <@42>", "new")
    assert back.submitter_id == 42


async def test_masterlist_parser_rejects_other_messages(monkeypatch):
    cog = _submissions_cog(monkeypatch, _text_channel())
    with pytest.raises(ValueError):
        await cog._masterlist_sub_make("just some chat", "new")
