import discord
from discord.ext import commands
import chat_exporter
import io

from features.general.general_constants import *


class General(commands.Cog, description="General commands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        brief="The All Might Supermod appears.",
        description="The All Might Supermod appears.",
    )
    async def hello(self, ctx: commands.Context):
        await ctx.send("It's fine now. Why? Because I am here!")

    @commands.command(
        brief="Archive a channel from its channel id.",
        description="Archive a channel from its channel id "
        "(e.g. ,archive 123456789012345678). If no channel id is given, "
        "the current channel will be archived.",
    )
    @commands.has_role(STAFF_ROLE)
    async def archive(self, ctx: commands.Context, channel_id=None):
        if channel_id == None:
            channel = ctx.channel
        else:
            channel = self.bot.get_channel(int(channel_id))

        if channel == None:
            await ctx.send("Please specify a valid channel id.")
            return

        transcript = await chat_exporter.export(channel)
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"{channel.name}.html",
        )

        await ctx.send(file=transcript_file)
