from os import getenv
from typing import Optional

from discord import Member, TextChannel
from discord.ext import commands
from discord.ext.commands import Bot


def get_and_verify_env(var_name: str) -> str:
    var = getenv(var_name)
    if var is None:
        raise RuntimeError(f"Environment variable {var_name} is not found")
    return var


def text_channel(bot: Bot, channel_id: int) -> Optional[TextChannel]:
    """
    Resolve a channel id to a TextChannel, or None if it is missing or not a
    text channel. Lets callers keep a simple `is None` guard while narrowing the
    broad get_channel() union for the type checker.
    """
    channel = bot.get_channel(channel_id)
    return channel if isinstance(channel, TextChannel) else None


def is_staff(role_id: int):
    """Pass for the bot owner or any guild member holding the staff role."""

    async def predicate(ctx: commands.Context) -> bool:
        if await ctx.bot.is_owner(ctx.author):
            return True
        author = ctx.author
        return isinstance(author, Member) and any(
            role.id == role_id for role in author.roles
        )

    return commands.check(predicate)
