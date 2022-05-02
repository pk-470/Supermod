# Library for Discord
from discord.ext import commands

# Album class
from classes.album_class import Album

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


# Setting
news_sheet = gsa.open_by_url(getenv("NEWS_SHEET_URL"))


class Newsletter(commands.Cog, description="Functions to fetch the weekly newsletter."):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief="Fetch a newsletter from any week (1/1/2021 onwards).",
        description="Fetch the newsletter from a particular week from 1/1/2021 onwards "
        "(optional argument: date in M/D/YYYY format). If date is missing, the current "
        "week's newsletter is returned.",
    )
    async def news(self, ctx, date_str=None):
        if date_str == None:
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
            await ctx.send(
                "To add a message to this week's official newsletter, "
                "write it after the 'news_full' command (e.g. news_full 'message')."
            )
            return
        else:
            date = pendulum.now("America/Toronto")
            sheet_data = news_sheet.sheet1.get_all_values()
            posts = newsletter_create(sheet_data, date, message)
            for post in posts:
                await ctx.send(post)

    @commands.command(
        brief="Split the albums in this week's newsletter by genre category.",
        description="Split the albums in this week's newsletter by genre category.",
    )
    async def news_by_genre(self, ctx):
        sheet_data = news_sheet.sheet1.get_all_values()
        genre_categories_posts = news_by_genre(sheet_data)
        for genre_category in genre_categories_posts:
            for post in genre_categories_posts[genre_category]:
                await ctx.send(post)


def news_get(sheet_data, week):
    releases = [
        release
        for release in sheet_data[5:]
        if release[0] and release[0] != "..." and week_check(release[2], week)
    ]
    albums = [
        Album(
            artist=release[0],
            title=release[1],
            genres=release[4],
            genre_categories=release[13],
            release_date=release[2],
            countries=release[6],
            length=release[3],
            ffo=release[7],
        )
        for release in releases
    ]

    return albums


def split_by_length(albums):
    # Organise albums by length in the newsletter.
    # Returns a string with all the albums organised.
    album_lengths = []
    for album in albums:
        if album.length not in album_lengths:
            album_lengths.append(album.length)
    album_lengths.sort()
    if "EP" in album_lengths:
        album_lengths.insert(0, album_lengths.pop(album_lengths.index("EP")))
    if "LP" in album_lengths:
        album_lengths.insert(0, album_lengths.pop(album_lengths.index("LP")))
    albums_by_length = []
    for length in album_lengths:
        albums_by_length.append(
            f"__*New {plural(length)}:*__\n"
            + "\n".join(
                [
                    album.news_format()
                    for album in albums
                    if album.length == length and album.news_format()
                ]
            )
        )

    return "\n\n".join(albums_by_length)


def newsletter_create(sheet_data, date, message=None):
    title_day, week = end_of_week(date)
    albums = news_get(sheet_data, week)
    if message == None:
        post_full = (
            "**__Omnivoracious Listeners New Music Newsletter (Week of "
            + title_day.strftime("%B")
            + " "
            + day_trim(title_day.strftime("%d"))
            + f"{ordinal(title_day.day)}):__**\n\n"
            + split_by_length(albums)
        )
    else:
        post_full = (
            "**__Omnivoracious Listeners New Music Newsletter (Week of "
            + title_day.strftime("%B")
            + " "
            + day_trim(title_day.strftime("%d"))
            + f"{ordinal(title_day.day)}):__**\n\n"
            + split_by_length(albums)
            + f"\n\n{message}\n<"
            + getenv("NEWS_SHEET_URL")
            + ">\n\nFeel free to contribute to our ever-growing newsletter:\n<"
            + getenv("NEWS_FORM_URL")
            + ">\n\nHappy Listening!"
        )

    return post_split(post_full, 2000)


def news_by_genre(sheet_data):
    # Organise albums by genre to be posted in the relevant genre category channels.
    # Returns a dictionary in the form {genre category : albums organised by length}.
    date = pendulum.now("America/Toronto")
    title_day, week = end_of_week(date)
    albums = news_get(sheet_data, week)
    album_genre_categories = []
    for album in albums:
        for genre_category in album.genre_categories:
            if genre_category not in album_genre_categories:
                album_genre_categories.append(genre_category)
    genre_categories_posts = {}
    for genre_category in album_genre_categories:
        albums_of_genre = [
            album for album in albums if genre_category in album.genre_categories
        ]
        genre_categories_posts[genre_category] = post_split(
            "**__Stuff you might be into this week ("
            + title_day.strftime("%B")
            + " "
            + day_trim(title_day.strftime("%d"))
            + f"{ordinal(title_day.day)}) ({genre_category}):__**\n\n"
            + split_by_length(albums_of_genre),
            2000,
        )

    return genre_categories_posts


def post_split(long_post, length):
    # Splits long posts.
    posts = [long_post]
    while len(long_post) > length:
        i = 1
        while i < length and long_post[length - i] != "\n":
            i = i + 1
        if i < length:
            split_at = length - i
        else:
            i = 1
            while i < length and long_post[length - i] not in (".", "?", "!"):
                i = i + 1
            split_at = length - i + 1
        posts.remove(long_post)
        posts.extend([long_post[:split_at], long_post[split_at + 1 :]])
        long_post = long_post[split_at + 1 :]

    return posts


# Week checks
def week_no(date):
    return (date - date.start_of("year")).days // 7 + 1


def end_of_week(date):
    week = week_no(date)
    days = 7 * week - 1
    return date.start_of("year").add(days=days), week


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
    if string[-1] in ("s", "x", "z") or string[-2:] in ("sh", "ch"):
        return f"{string}es"
    else:
        return f"{string}s"


def day_trim(day):
    if day[0] == "0":
        day = day[1:]
    return day


# Add cog to bot
def setup(bot):
    bot.add_cog(Newsletter(bot))
