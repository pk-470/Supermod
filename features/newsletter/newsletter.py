from discord.ext import commands
import pendulum

from features.newsletter.news_constants import *
from features.newsletter.news_utils import *


class Newsletter(commands.Cog, description="Functions to fetch the weekly newsletter."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        brief="Fetch a newsletter from any week (1/1/2021 onwards).",
        description="Fetch the newsletter from a particular week from 1/1/2021 onwards "
        "(optional argument: date in M/D/YYYY format). If date is missing, the current "
        "week's newsletter is returned.",
    )
    async def news(self, ctx: commands.Context, date_str=None):
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
            except:
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
    async def news_full(self, ctx: commands.Context, *, ending_message=None):
        if ending_message is None:
            await ctx.send(
                "To add a message to this week's official newsletter, "
                "write it after the 'news_full' command (e.g. news_full 'message')."
            )
            return
        else:
            date = pendulum.now("America/Toronto")
            sheet_data = NEWS_SHEET.sheet1.get_all_values()
            await newsletter_post(ctx, sheet_data, date, ending_message)

    @commands.command(
        brief="Split the albums in this week's newsletter by genre category.",
        description="Split the albums in this week's newsletter by genre category. "
        "Add the word 'post' as an argument to post each genre newsletter in its "
        "respective genre channel.",
    )
    @commands.has_role(STAFF_ROLE)
    async def news_by_genre(self, ctx: commands.Context, arg=None):
        sheet_data = NEWS_SHEET.sheet1.get_all_values()
        genre_categories_posts, errors_message = news_by_genre(sheet_data)
        for genre_category in genre_categories_posts:
            posts = post_split(genre_categories_posts[genre_category], 2000)
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
