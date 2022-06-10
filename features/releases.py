# Library for Discord
from discord.ext import commands

# Release class
from classes.release_class import Release

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
NEWS_SHEET = gsa.open_by_url(getenv("NEWS_SHEET_URL"))

GENRE_CHANNELS = {
    "Experimental Rock": int(getenv("EXPERIMENTAL_ROCK")),
    "Hard Rock": int(getenv("HARD_ROCK")),
    "Soft Rock": int(getenv("SOFT_ROCK")),
    "Punk": int(getenv("PUNK")),
    "Core": int(getenv("CORE")),
    "Metal": int(getenv("METAL")),
    "Extreme Metal": int(getenv("EXTREME_METAL")),
    "Classical / Jazz / Blues": int(getenv("CLASSICAL_JAZZ_BLUES")),
    "Country / Folk": int(getenv("COUNTRY_FOLK")),
    "Electronic": int(getenv("ELECTRONIC")),
    "Pop / Hip Hop": int(getenv("POP_HIP_HOP")),
}


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
    async def news_full(self, ctx, *, message=None):
        if message is None:
            await ctx.send(
                "To add a message to this week's official newsletter, "
                "write it after the 'news_full' command (e.g. news_full 'message')."
            )
            return
        else:
            date = pendulum.now("America/Toronto")
            sheet_data = NEWS_SHEET.sheet1.get_all_values()
            await newsletter_post(ctx, sheet_data, date, message)

    @commands.command(
        brief="Split the albums in this week's newsletter by genre category.",
        description="Split the albums in this week's newsletter by genre category. "
        "Add the word 'post' as an argument to post each genre newsletter in its "
        "respective genre channel.",
    )
    async def news_by_genre(self, ctx, arg=None):
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


def news_get(sheet_data, week):
    releases = [
        release
        for release in sheet_data[5:]
        if release[0] and release[0] != "..." and week_check(release[2], week)
    ]
    albums = [
        Release(
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
    # Organise albums by length in the newsletter. Returns a string with
    # with all the albums organised and a list with possible errors.
    albums_by_length = {"LP": [], "EP": []}
    errors = []
    for album in albums:
        if not album.news_format().startswith("**ERROR:**"):
            if album.length in albums_by_length:
                albums_by_length[album.length].append(album.news_format())
            else:
                albums_by_length[album.length] = [album.news_format()]
        else:
            errors.append(album.news_format())
    if not albums_by_length["LP"]:
        albums_by_length.pop("LP")
    if not albums_by_length["EP"]:
        albums_by_length.pop("EP")
    news_message = "\n\n".join(
        [
            f"__*New {plural(length)}:*__\n"
            + "\n".join(
                [formatted_album for formatted_album in albums_by_length[length]]
            )
            for length in albums_by_length
        ]
    )

    return news_message, errors


async def newsletter_post(channel, sheet_data, date, message=None):
    title_day, week = end_of_week(date)
    albums = news_get(sheet_data, week)
    news_message, errors = split_by_length(albums)
    if message is None:
        post_full = (
            "**__Omnivoracious Listeners New Music Newsletter (Week of "
            + title_day.strftime("%B")
            + " "
            + day_trim(title_day.strftime("%d"))
            + f"{ordinal(title_day.day)}):__**\n\n"
            + news_message
        )
    else:
        post_full = (
            "**__Omnivoracious Listeners New Music Newsletter (Week of "
            + title_day.strftime("%B")
            + " "
            + day_trim(title_day.strftime("%d"))
            + f"{ordinal(title_day.day)}):__**\n\n"
            + news_message
            + f"\n\n{message}\n<"
            + getenv("NEWS_SHEET_URL")
            + ">\n\nFeel free to contribute to our ever-growing newsletter:\n<"
            + getenv("NEWS_FORM_URL")
            + ">\n\nHappy Listening!"
        )

    if errors:
        errors_message = "\n".join(errors)
    else:
        errors_message = ""

    posts = post_split(post_full, 2000)
    for post in posts:
        await channel.send(post)
    if errors_message:
        await channel.send(errors_message)


def news_by_genre(sheet_data):
    # Organise albums by genre to be posted in the relevant genre category channels.
    # Returns a dictionary in the form {genre category : albums organised by length}
    # and a string containing all errors.
    date = pendulum.now("America/Toronto")
    title_day, week = end_of_week(date)
    albums = news_get(sheet_data, week)
    albums_by_genre_category = {}
    for album in albums:
        for genre_category in album.genre_categories:
            if genre_category in albums_by_genre_category:
                albums_by_genre_category[genre_category].append(album)
            else:
                albums_by_genre_category[genre_category] = [album]

    genre_categories_posts = {}
    all_errors = []
    for genre_category in albums_by_genre_category:
        news_message, errors = split_by_length(albums_by_genre_category[genre_category])
        genre_categories_posts[genre_category] = (
            "**__Stuff you might be into this week ("
            + title_day.strftime("%B")
            + " "
            + day_trim(title_day.strftime("%d"))
            + f"{ordinal(title_day.day)}) ({genre_category}):__**\n\n"
            + news_message
        )
        all_errors.extend([error for error in errors if error not in all_errors])

    if all_errors:
        errors_message = "\n".join([all_errors])
    else:
        errors_message = ""

    return genre_categories_posts, errors_message


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
