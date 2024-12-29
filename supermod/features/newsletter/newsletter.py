from typing import Optional

import pendulum
from discord.ext import commands

from .news_constants import *
from .news_utils import *


class Newsletter(commands.Cog, description="Functions to fetch the weekly newsletter."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        brief="Fetch a newsletter from any week (1/1/2021 onwards).",
        description="Fetch the newsletter from a particular week from 1/1/2021 onwards "
        + "(optional argument: date in M/D/YYYY format). If date is missing, the current "
        + "week's newsletter is returned.",
    )
    async def news(self, ctx: commands.Context, date_str: Optional[str] = None):
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
                print_info(e)
                await ctx.send(
                    "Please make sure your date is in the correct format (M/D/YYYY)."
                )
                return

        sheet = f"{date.year} OL Rock Albums List"
        sheet_data = NEWS_SHEET.worksheet(sheet).get_all_values()
        await newsletter_post(ctx, sheet_data, date)

    @commands.command(
        brief="Add a message to this week's official newsletter.",
        description="Add a message to this week's official newsletter (argument: message).",
    )
    @commands.has_role(STAFF_ROLE)
    async def news_full(
        self, ctx: commands.Context, *, ending_message: Optional[str] = None
    ):
        if ending_message is None:
            await ctx.send(
                "To add a message to this week's official newsletter, "
                + "write it after the 'news_full' command (e.g. news_full 'message')."
            )
            return

        date = pendulum.now("America/Toronto")
        sheet_data = NEWS_SHEET.sheet1.get_all_values()
        await newsletter_post(ctx, sheet_data, date, ending_message)

    @commands.command(
        brief="Add a message to this week's official newsletter and format it for reddit.",
        description="Add a message to this week's official newsletter and format it for reddit. (argument: message).",
    )
    @commands.has_role(STAFF_ROLE)
    async def news_full_reddit(
        self, ctx: commands.Context, *, ending_message: Optional[str] = None
    ):
        if ending_message is None:
            await ctx.send(
                "To add a message to this week's official newsletter, "
                + "write it after the 'news_full' command (e.g. news_full 'message')."
            )
            return

        date = pendulum.now("America/Toronto")
        sheet_data = NEWS_SHEET.sheet1.get_all_values()
        await newsletter_post(
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
    @commands.has_role(STAFF_ROLE)
    async def news_by_genre(self, ctx: commands.Context, arg: Optional[str] = None):
        sheet_data = NEWS_SHEET.sheet1.get_all_values()
        genre_categories_posts, errors_message = news_by_genre(sheet_data)
        for genre_category, long_post in genre_categories_posts.items():
            posts = post_split(long_post, 2000)
            for post in posts:
                if arg == "post":
                    await self.bot.get_channel(GENRE_CHANNELS[genre_category]).send(
                        post
                    )
                else:
                    await ctx.send(post)
        if arg == "post":
            await ctx.send(
                "The genre newsletters have been posted in their respective channels."
            )
        if errors_message:
            await ctx.send(errors_message)
