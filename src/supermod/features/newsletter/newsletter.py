import logging
from typing import Optional

import gspread
import pendulum
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Context

from supermod._utils import is_staff, text_channel
from supermod.features.newsletter._constants import *
from supermod.features.newsletter._utils import *

logger = logging.getLogger(__name__)


class Newsletter(Cog, description="Functions to fetch the weekly newsletter."):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(
        brief="Fetch a newsletter from any week (1/1/2021 onwards).",
        description="Fetch the newsletter from a particular week from 1/1/2021 onwards "
        + "(optional argument: date in M/D/YYYY format). If date is missing, the current "
        + "week's newsletter is returned.",
    )
    async def news(self, ctx: Context, date_str: Optional[str] = None):
        if date_str is None:
            date = pendulum.now("America/Toronto")
        else:
            try:
                date = pendulum.from_format(date_str, "M/D/YYYY")
                if date.year < 2021:
                    await ctx.send(
                        "The OL Newsletter only contains albums released in 2021 or later."
                    )
                    return
            except Exception as e:
                # A mistyped date is user-input validation, not an error worth
                # a traceback; the user already gets a corrective reply below.
                logger.warning("Could not parse newsletter date %r: %s", date_str, e)
                await ctx.send(
                    "Please make sure your date is in the correct format (M/D/YYYY)."
                )
                return

        sheet = f"{date.year} OL Rock Albums List"
        try:
            worksheet = news_sheet().worksheet(sheet)
        except gspread.exceptions.WorksheetNotFound:
            await ctx.send(f"No newsletter exists for {date.year}.")
            return
        sheet_data = worksheet.get_all_values()
        await self._newsletter_post(ctx, sheet_data, date)

    @commands.command(
        brief="Add a message to this week's official newsletter.",
        description="Add a message to this week's official newsletter (argument: message).",
    )
    @is_staff(STAFF_ROLE)
    async def news_full(self, ctx: Context, *, ending_message: Optional[str] = None):
        if ending_message is None:
            await ctx.send(
                "To add a message to this week's official newsletter, "
                + "write it after the 'news_full' command (e.g. news_full 'message')."
            )
            return

        date = pendulum.now("America/Toronto")
        sheet_data = news_sheet().sheet1.get_all_values()
        await self._newsletter_post(ctx, sheet_data, date, ending_message)

    @commands.command(
        brief="Add a message to this week's official newsletter and format it for reddit.",
        description="Add a message to this week's official newsletter and format it for reddit. (argument: message).",
    )
    @is_staff(STAFF_ROLE)
    async def news_full_reddit(
        self, ctx: Context, *, ending_message: Optional[str] = None
    ):
        if ending_message is None:
            await ctx.send(
                "To add a message to this week's official newsletter, "
                + "write it after the 'news_full_reddit' command (e.g. news_full_reddit 'message')."
            )
            return

        date = pendulum.now("America/Toronto")
        sheet_data = news_sheet().sheet1.get_all_values()
        await self._newsletter_post(
            ctx,
            sheet_data,
            date,
            ending_message,
            double_spacing=True,
            contribute_message=False,
            spreadsheet_link=False,
            discord_invite=True,
        )

    @commands.command(
        brief="Split the albums in this week's newsletter by genre category.",
        description="Split the albums in this week's newsletter by genre category. "
        + "Add the word 'post' as an argument to post each genre newsletter in its "
        + "respective genre channel.",
    )
    @is_staff(STAFF_ROLE)
    async def news_by_genre(self, ctx: Context, arg: Optional[str] = None):
        sheet_data = news_sheet().sheet1.get_all_values()
        genre_categories_posts, errors_message = news_by_genre(sheet_data)
        for genre_category, long_post in genre_categories_posts.items():
            posts = post_split(long_post, 2000)
            for post in posts:
                if arg == "post":
                    channel_id = GENRE_CHANNELS.get(genre_category)
                    if channel_id is None:
                        logger.warning(
                            "No genre channel configured for %r.", genre_category
                        )
                        continue
                    channel = text_channel(self.bot, channel_id)
                    if channel is None:
                        logger.warning(
                            "Could not resolve channel %s for %r.",
                            channel_id,
                            genre_category,
                        )
                        continue
                    await channel.send(post)
                else:
                    await ctx.send(post)
        if arg == "post":
            await ctx.send(
                "The genre newsletters have been posted in their respective channels."
            )
        if errors_message:
            for chunk in post_split(errors_message, 2000):
                await ctx.send(chunk)

    async def _newsletter_post(
        self,
        ctx: Context,
        sheet_data: list[list[str]],
        date: DateTime,
        ending_message: Optional[str] = None,
        **kwargs,
    ) -> None:
        posts, errors_message = newsletter_create(
            sheet_data, date, ending_message, **kwargs
        )
        for post in posts:
            await ctx.send(post)
        if errors_message:
            for chunk in post_split(errors_message, 2000):
                await ctx.send(chunk)
