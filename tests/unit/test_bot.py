"""
Tests for the bot core: the bot-wide mention rules, the replies to command
errors, and feature discovery and loading.
"""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from discord.ext import commands

from supermod import _mode_setup
from supermod import bot as bot_mod
from tests.fakes import make_ctx

FEATURES = {
    "general",
    "newsletter",
    "promotions",
    "qotd",
    "submissions",
    "submissions_status",
}


@pytest.fixture
def supermod() -> bot_mod.Supermod:
    return bot_mod.Supermod()


# --- mentions ------------------------------------------------------------------


def test_default_mentions_allow_users_but_not_roles_or_everyone(supermod):
    # Role pings must be opted into per message (as the Listeners announcements
    # do); a blanket AllowedMentions.none() silently broke them once.
    mentions = supermod.allowed_mentions
    assert mentions is not None
    assert mentions.everyone is False
    assert mentions.roles is False
    assert mentions.users is True


# --- command errors ----------------------------------------------------------


async def test_unknown_command_is_ignored(supermod):
    ctx = make_ctx()
    await supermod.on_command_error(ctx, commands.CommandNotFound())
    assert ctx.sent == []


async def test_failed_check_replies_no_permission(supermod):
    ctx = make_ctx()
    await supermod.on_command_error(ctx, commands.CheckFailure())
    assert ctx.sent == ["You don't have permission to use this command."]


async def test_missing_argument_names_it(supermod):
    ctx = make_ctx()
    param = MagicMock()
    param.name = "masterlist"
    await supermod.on_command_error(ctx, commands.MissingRequiredArgument(param))
    assert ctx.sent == ["Missing required argument: masterlist."]


async def test_unexpected_error_is_logged_and_reported(supermod, caplog):
    ctx = make_ctx()
    ctx.command = MagicMock(qualified_name="subs")
    error = commands.CommandInvokeError(RuntimeError("boom"))

    await supermod.on_command_error(ctx, error)

    assert "`subs`" in ctx.sent[0]
    assert "boom" in caplog.text  # the original exception, not the wrapper


# --- feature loading ---------------------------------------------------------


async def test_load_features_loads_every_feature_package(supermod):
    supermod.load_extension = AsyncMock()

    await supermod.load_features()

    loaded = {call.args[0] for call in supermod.load_extension.await_args_list}
    assert loaded == {f"supermod.features.{name}" for name in FEATURES}


async def test_one_failing_feature_does_not_stop_the_others(supermod, caplog):
    async def load(name):
        if name.endswith(".qotd"):
            raise RuntimeError("bad feature")

    supermod.load_extension = AsyncMock(side_effect=load)

    await supermod.load_features()

    assert supermod.load_extension.await_count == len(FEATURES)
    assert "Failed to load feature qotd" in caplog.text


async def test_all_features_load_for_real(supermod, monkeypatch, tmp_path):
    # Real imports and setup(); local mode keeps the background loops stopped.
    marker = tmp_path / ".local"
    marker.write_text("")
    monkeypatch.setattr(_mode_setup, "LOCAL_MARKER", marker)
    _mode_setup.is_local.cache_clear()
    saved = {k: v for k, v in sys.modules.items() if k.startswith("supermod.features")}
    try:
        await supermod.load_features()
    finally:
        sys.modules.update(saved)
        _mode_setup.is_local.cache_clear()

    assert set(supermod.cogs) == {
        "General",
        "Newsletter",
        "Promotions",
        "QOTD",
        "Album Submissions",
        "SubmissionsStatus",
    }
