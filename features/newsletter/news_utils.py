from discord.ext.commands import Context
from os import getenv
import pendulum
from pendulum.datetime import DateTime

from album_classes import Release


def news_get(sheet_data, week):
    releases_as_lists = [
        release_as_list
        for release_as_list in sheet_data[5:]
        if release_as_list[0]
        and release_as_list[0] != "..."
        and week_check(release_as_list[2], week)
    ]
    releases = [
        Release(
            artist=release_as_list[0],
            title=release_as_list[1],
            genres=release_as_list[4],
            genre_categories=release_as_list[11],
            release_date=release_as_list[2],
            countries=release_as_list[6],
            length=release_as_list[3],
            ffo=release_as_list[7],
        )
        for release_as_list in releases_as_lists
    ]

    return releases


def split_by_length(releases: list[Release]):
    """
    Organise albums by length in the newsletter. Returns a string with
    with all the albums organised and a list with possible errors.
    """
    releases_by_length = {"LP": [], "EP": []}
    errors = []
    for release in releases:
        if not release.news_format().startswith("**ERROR:**"):
            if release.length in releases_by_length:
                releases_by_length[release.length].append(release.news_format())
            else:
                releases_by_length[release.length] = [release.news_format()]
        else:
            errors.append(release.news_format())
    if not releases_by_length["LP"]:
        releases_by_length.pop("LP")
    if not releases_by_length["EP"]:
        releases_by_length.pop("EP")
    news_message = "\n\n".join(
        [
            f"__*New {plural(length)}:*__"
            "\n"
            + "\n".join(
                [release_formatted for release_formatted in releases_by_length[length]]
            )
            for length in releases_by_length
        ]
    )

    return news_message, errors


def newsletter_create(sheet_data, date: DateTime, ending_message=None):
    title_day, week = end_of_week(date)
    albums = news_get(sheet_data, week)
    news_message, errors = split_by_length(albums)

    # Title variables
    month = title_day.strftime("%B")
    day_ordinal = day_trim(title_day.strftime("%d")) + ordinal(title_day.day)

    post_main = (
        f"**__Omnivoracious Listeners New Music Newsletter (Week of {month} {day_ordinal}):__**"
        "\n\n"
        f"{news_message}"
    )

    if ending_message is None:
        post_full = post_main
    else:
        post_full = (
            f"{post_main}"
            "\n\n"
            f"{ending_message}"
            "\n"
            f"<{getenv('NEWS_SHEET_URL')}>"
            "\n\n"
            "Feel free to contribute to our ever-growing newsletter:"
            "\n"
            f"<{getenv('NEWS_FORM_URL')}>"
            "\n\n"
            "Happy Listening!"
        )

    posts = post_split(post_full, 2000)

    if errors:
        errors_message = "\n".join(errors)
    else:
        errors_message = ""

    return posts, errors_message


async def newsletter_post(ctx: Context, sheet_data, date, ending_message=None):
    posts, errors_message = newsletter_create(sheet_data, date, ending_message)
    for post in posts:
        await ctx.send(post)
    if errors_message:
        await ctx.send(errors_message)


def news_by_genre(sheet_data):
    """
    Organise albums by genre to be posted in the relevant genre category channels.
    Returns a dictionary in the form {genre category : albums organised by length}
    and a string containing all errors.
    """
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

        # Title variables
        month = title_day.strftime("%B")
        day_ordinal = day_trim(title_day.strftime("%d")) + ordinal(title_day.day)

        genre_categories_posts[genre_category] = (
            f"**__Stuff you might be into this week ({month} {day_ordinal}) ({genre_category}):__**"
            "\n\n"
            f"{news_message}"
        )
        all_errors.extend([error for error in errors if error not in all_errors])

    if all_errors:
        errors_message = "\n".join([all_errors])
    else:
        errors_message = ""

    return genre_categories_posts, errors_message


def post_split(long_post, max_post_length):
    """
    Splits long posts.
    """
    posts = [long_post]
    while len(long_post) > max_post_length:
        i = 1
        while i < max_post_length and long_post[max_post_length - i] != "\n":
            i = i + 1
        if i < max_post_length:
            split_at = max_post_length - i
        else:
            i = 1
            while i < max_post_length and long_post[max_post_length - i] not in (
                ".",
                "?",
                "!",
            ):
                i = i + 1
            split_at = max_post_length - i + 1
        posts.remove(long_post)
        posts.extend([long_post[:split_at], long_post[split_at + 1 :]])
        long_post = long_post[split_at + 1 :]

    return posts


# Week checks
def week_no(date: DateTime):
    return (date - date.start_of("year")).days // 7 + 1


def end_of_week(date: DateTime):
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
