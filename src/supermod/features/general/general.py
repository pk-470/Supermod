import io
import logging
from typing import Optional

import chat_exporter
import discord
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context

from supermod._utils import is_staff
from supermod.features.general._constants import *

logger = logging.getLogger(__name__)


class General(Cog, description="General commands"):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        brief="The All Might Supermod appears.",
        description="The All Might Supermod appears.",
    )
    async def hello(self, ctx: Context):
        await ctx.send("It's fine now. Why? Because I am here!")

    @commands.command(
        brief="Archive a channel from its channel id.",
        description="Archive a channel from its channel id "
        + "(e.g. ,archive 123456789012345678). If no channel id is given, "
        + "the current channel will be archived.",
    )
    @is_staff(STAFF_ROLE)
    async def archive(self, ctx: Context, channel_id: Optional[str] = None) -> None:
        if channel_id is None:
            channel = ctx.channel
        else:
            try:
                channel = self.bot.get_channel(int(channel_id))
            except ValueError:
                await ctx.send("Please specify a valid channel id.")
                return

        if not isinstance(channel, discord.TextChannel):
            await ctx.send("Please specify a valid text channel id.")
            return

        # export() swallows errors and returns None unless raise_exceptions=True,
        # so opt in and report failures rather than silently doing nothing. The
        # full-history export can be slow, so show a typing indicator meanwhile.
        try:
            async with ctx.typing():
                transcript = await chat_exporter.export(
                    channel, bot=self.bot, raise_exceptions=True
                )
        except Exception:
            logger.exception("Failed to export channel %s for archiving.", channel.id)
            await ctx.send(
                f"Couldn't archive {channel.mention} — the export failed. "
                "The error has been logged."
            )
            return

        if not transcript:
            await ctx.send(f"There's nothing to archive in {channel.mention}.")
            return

        transcript += (
            "<style>*{-webkit-user-select:text !important;"
            "-moz-user-select:text !important;-ms-user-select:text !important;"
            "user-select:text !important;}</style>"
        )
        await ctx.send(
            file=discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"{channel.name}.html",
            )
        )
