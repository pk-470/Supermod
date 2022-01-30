# Library for date manipulation
import pendulum

# Album class
from album_class import album

# Libraries to load hidden data from .env
from os import getenv
from dotenv import load_dotenv


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

    load_dotenv()
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


# Proper grammar for the newsletter:
def ordinal(num):
    if num % 10 == 1:
        return "st"
    if num % 10 == 2:
        return "nd"
    if num % 10 == 3:
        return "rd"
    else:
        return "th"


def plural(string):
    if string[-1] in ["s", "sh", "ch", "x", "z"]:
        return string + "es"
    else:
        return string + "s"
