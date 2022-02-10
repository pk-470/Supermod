# Library for Discord
from discord.ext import commands

# Album class
from classes.album_class import album

# Library for date manipulation
import pendulum

# Library to load tokens
from os import getenv

# Library for handling Google spreadsheets
import gspread

# Import data according to local_mode status
local_mode = open("mode_switch.txt", "r").read()

if local_mode == "ON":
    from dotenv import load_dotenv

    load_dotenv("tokens/.env")

    gsa = gspread.service_account("tokens/service_account.json")
else:
    from json import loads

    gsa = gspread.service_account_from_dict(loads(getenv("SERVICE_ACCOUNT_CRED")))

news_sheet = gsa.open_by_url(getenv("NEWS_SHEET_URL"))


class Newsletter(
    commands.Cog, description="Functions to setup and create the weekly newsletter."
):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief="Fetch a newsletter from any week (1/1/2021 onwards).",
        description="Fetch the newsletter from a particular week from 1/1/2021 onwards (optional "
        + "argument: date in M/D/YYYY format). If date is missing, the current week's newsletter "
        + "is returned.",
    )
    async def news(self, ctx, date_str=None):
        if date_str == None:
            date = pendulum.today()
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

        sheet = str(date.year) + " OL Rock Albums List"
        sheet_data = news_sheet.worksheet(sheet).get_all_values()
        posts = newsletter_create(sheet_data, date)
        for post in posts:
            await ctx.send(post)

    @commands.command(
        brief="Add a message to this week's official newsletter.",
        description="Add a message to this week's official newsletter (argument: message).",
    )
    async def news_full(self, ctx, *, message=None):
        if message == None:
            await ctx.send("What will be this week's newsletter message?")
            return
        else:
            date = pendulum.today()
            sheet_data = news_sheet.sheet1.get_all_values()
            posts = newsletter_create(sheet_data, date, message)
            for post in posts:
                await ctx.send(post)


def news_get(sheet_data, week):
    releases = [
        release
        for release in sheet_data[5:]
        if release[0] and release[0] != "..." and week_check(release[2], week)
    ]
    albums = [
        album(
            artists=release[0],
            title=release[1],
            genres=release[4],
            release_date=release[2],
            countries=release[6],
            length=release[3],
            FFO=release[7],
        )
        for release in releases
    ]

    return albums


def newsletter_create(sheet_data, date, message=None):
    week = week_no(date)
    albums = news_get(sheet_data, week)
    album_lengths = []
    [
        album_lengths.append(album.length)
        for album in albums
        if album.length not in album_lengths
    ]
    album_lengths.sort()
    if "EP" in album_lengths:
        album_lengths.insert(0, album_lengths.pop(album_lengths.index("EP")))
    if "LP" in album_lengths:
        album_lengths.insert(0, album_lengths.pop(album_lengths.index("LP")))
    albums_by_length = []
    for length in album_lengths:
        albums_by_length.append(
            "__*New "
            + plural(length)
            + ":*__\n"
            + "\n".join(
                [
                    album.news_format()
                    for album in albums
                    if album.length == length and album.news_format()
                ]
            )
        )

    title_day = end_of_week(date, week)
    if message == None:
        post_full = (
            "**__Omnivoracious Listeners New Music Newsletter (Week of "
            + title_day.strftime("%B")
            + " "
            + title_day.strftime("%#d")
            + ordinal(title_day.day)
            + "):__**\n\n"
            + "\n\n".join(albums_by_length)
        )
    else:
        post_full = (
            "**__Omnivoracious Listeners New Music Newsletter (Week of "
            + title_day.strftime("%B")
            + " "
            + title_day.strftime("%#d")
            + ordinal(title_day.day)
            + "):__**\n\n"
            + "\n\n".join(albums_by_length)
            + "\n\n"
            + message
            + "\n<"
            + getenv("NEWS_SHEET_URL")
            + ">\n\nFeel free to contribute to our ever-growing newsletter:\n<"
            + getenv("NEWS_FORM_URL")
            + ">\n\nHappy Listening!"
        )

    return post_split(post_full)


# Split long posts
def post_split(long_post):
    posts = [long_post]
    while len(long_post) > 2000:
        i = 1
        while long_post[2000 - i] != "\n":
            i = i + 1
        split_at = 2000 - i
        posts.remove(long_post)
        posts.extend([long_post[:split_at], long_post[split_at:]])
        long_post = long_post[split_at:]

    return posts


# Week checks
def week_no(date):
    return (date - date.start_of("year")).days // 7 + 1


def end_of_week(date, week):
    days = 7 * week - 1
    return date.start_of("year").add(days=days)


def week_check(value, week):
    try:
        if week_no(pendulum.from_format(value, "M/D/YYYY")) == week:
            return True
        else:
            return False
    except:
        return False


# Proper grammar for the newsletter
def ordinal(num):
    if num in (1, 21, 31):
        return "st"
    elif num in (2, 22):
        return "nd"
    elif num in (3, 23):
        return "rd"
    else:
        return "th"


def plural(string):
    if string[-1] in ["s", "sh", "ch", "x", "z"]:
        return string + "es"
    else:
        return string + "s"


# Add cog to bot
def setup(bot):
    bot.add_cog(Newsletter(bot))
