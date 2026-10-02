"""
Tests for the ``,subs`` approval flow: fetching unreacted submissions from
#submissions, warning about problem ones, and acting on the staff reply
(ok / reject / halt / unhalt). Sheets are FakeWorksheets, channels are mocks.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from supermod.features.submissions import _utils as subs_utils
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


def submission(content: str, author_id: int, halted: bool = False):
    """A #submissions message double, optionally carrying the halt reaction."""
    msg = make_message(content, author_id=author_id, author_name=f"user{author_id}")
    msg.reactions = [MagicMock(emoji="🇭")] if halted else []
    msg.add_reaction = AsyncMock()
    msg.clear_reaction = AsyncMock()
    return msg


class Harness:
    """A Submissions cog wired to fake sheets and channels."""

    def __init__(self, monkeypatch, messages, discussed=()):
        monkeypatch.setattr(submissions_mod, "is_local", lambda: True)

        self.sheets = FakeWorksheet(title="SUBS")
        for name in submissions_mod.MASTERLIST_CHANNEL_DICT:
            self.sheets.add_worksheet(
                name.upper(), FakeWorksheet([SUBS_HEADER], title=name.upper())
            )
        albums = FakeWorksheet([["Title", "Artist", "Week"], *discussed])
        monkeypatch.setattr(submissions_mod, "subs_sheet", lambda: self.sheets)
        monkeypatch.setattr(subs_utils, "subs_sheet", lambda: self.sheets)
        monkeypatch.setattr(subs_utils, "albums_wks", lambda: albums)

        submissions_channel = MagicMock(spec=discord.TextChannel)

        async def history(*args, **kwargs):
            for msg in messages:
                yield msg

        submissions_channel.history = history
        self.masterlists: dict[str, Any] = {}
        channels: dict[int, Any] = {
            submissions_mod.SUBMISSIONS_CHANNEL: submissions_channel
        }
        for name, channel_id in submissions_mod.MASTERLIST_CHANNEL_DICT.items():
            channel = MagicMock(spec=discord.TextChannel)
            channel.send = AsyncMock(return_value=MagicMock(id=500))
            self.masterlists[name] = channels[channel_id] = channel

        self.bot: Any = MagicMock()
        self.bot.get_channel.side_effect = channels.get
        self.cog = submissions_mod.Submissions(self.bot)
        self.ctx = make_ctx()

    async def run(self, reply: str, masterlist: str | None = None) -> None:
        """Run ``,subs [masterlist]`` and answer the prompt with ``reply``."""
        self.bot.wait_for = AsyncMock(return_value=make_message(reply))
        command: Any = submissions_mod.Submissions.subs
        await command.callback(self.cog, self.ctx, masterlist)

    def said(self, text: str) -> bool:
        return any(text in str(sent) for sent in self.ctx.sent)


async def test_ok_approves_only_submissions_without_warnings(monkeypatch):
    clean = submission("Clean Album // Band // 2020 // Rock // new", 11)
    discussed = submission("Old Favourite // Classic Band // 1990 // Rock // new", 12)
    h = Harness(
        monkeypatch,
        [clean, discussed],
        discussed=[["Old Favourite", "Classic Band", "42"]],
    )

    await h.run("ok")

    assert h.said("discussed already on week 42")
    new = h.masterlists["new"]
    new.send.assert_awaited_once()
    assert new.send.await_args.args[0] == "Clean Album _by_ Band (2020) (Rock) <@!11>"
    clean.add_reaction.assert_awaited_once_with("🆗")
    discussed.add_reaction.assert_not_awaited()
    assert h.sheets.worksheet("NEW").rows[1][:2] == ["Clean Album", "Band"]


async def test_ok_with_masterlist_only_touches_that_list(monkeypatch):
    for_new = submission("Fresh // Band // 2026 // Rock // new", 11)
    for_modern = submission("Recent // Other // 2015 // Pop // modern", 12)
    h = Harness(monkeypatch, [for_new, for_modern])

    await h.run("ok", masterlist="new")

    h.masterlists["new"].send.assert_awaited_once()
    h.masterlists["modern"].send.assert_not_awaited()
    for_modern.add_reaction.assert_not_awaited()
    assert h.said("added to the NEW masterlist")


async def test_reject_marks_the_listed_numbers(monkeypatch):
    msgs = [
        submission(f"Album {i} // Band // 2020 // Rock // new", i) for i in (1, 2, 3)
    ]
    h = Harness(monkeypatch, msgs)

    await h.run("reject 1, 3")

    msgs[0].add_reaction.assert_awaited_once_with("❌")
    msgs[1].add_reaction.assert_not_awaited()
    msgs[2].add_reaction.assert_awaited_once_with("❌")
    assert h.said("Albums 1, 3 were rejected.")


async def test_unknown_number_changes_nothing(monkeypatch):
    msgs = [submission(f"Album {i} // Band // 2020 // Rock // new", i) for i in (1, 2)]
    h = Harness(monkeypatch, msgs)

    await h.run("reject 1, 9")

    # The whole reply is rejected before any reaction is added.
    for msg in msgs:
        msg.add_reaction.assert_not_awaited()
    assert h.said("Something went wrong")


async def test_halt_marks_the_listed_number(monkeypatch):
    msgs = [submission(f"Album {i} // Band // 2020 // Rock // new", i) for i in (1, 2)]
    h = Harness(monkeypatch, msgs)

    await h.run("halt 2")

    msgs[1].add_reaction.assert_awaited_once_with("🇭")
    msgs[0].add_reaction.assert_not_awaited()
    assert h.said("Album 2 was halted.")


async def test_halted_lists_only_halted_and_unhalt_clears_them(monkeypatch):
    halted = submission("Paused // Band // 2020 // Rock // new", 1, halted=True)
    fresh = submission("Fresh // Band // 2020 // Rock // new", 2)
    h = Harness(monkeypatch, [halted, fresh])

    await h.run("unhalt 1", masterlist="halted")

    assert h.said("Paused")
    assert not h.said("Fresh")
    halted.clear_reaction.assert_awaited_once_with("🇭")
    assert h.said("Album 1 was unhalted.")


async def test_error_lists_unparseable_messages_and_refuses_ok(monkeypatch):
    broken = submission("just some chat, not a submission", 1)
    fine = submission("Album // Band // 2020 // Rock // new", 2)
    h = Harness(monkeypatch, [broken, fine])

    await h.run("ok", masterlist="error")

    assert h.said(f"Something went wrong with submission <{broken.jump_url}>")
    assert h.said("I can't add submissions with errors")
    h.masterlists["new"].send.assert_not_awaited()


@pytest.mark.parametrize("masterlist", [None, "new"])
async def test_nothing_new_says_so(monkeypatch, masterlist):
    already_handled = submission("Album // Band // 2020 // Rock // new", 1)
    already_handled.reactions = [MagicMock(emoji="🆗")]
    h = Harness(monkeypatch, [already_handled])

    await h.run("ok", masterlist=masterlist)

    assert h.said("There are no new submissions")
    h.bot.wait_for.assert_not_awaited()
