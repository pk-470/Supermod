# Titlecase
from titlecase import titlecase

# Genre data
from data.genres import *


class Album:
    def __init__(
        self,
        artist,
        title,
        genres,
        release_date,
        genre_categories=None,
        countries=None,
        length=None,
        ffo=None,
    ):
        self.artist = make_title(artist)
        self.title = make_title(title)
        self.genres = handle_genres(genres)
        self.genre_categories = handle_genre_categories(genre_categories)
        self.length = handle_length(length)
        self.release_date = remove_spaces(release_date)
        self.countries = handle_input(countries)
        self.ffo = handle_input(ffo)


def remove_spaces(string):
    if not string:
        return None
    string = str(string)
    if string:
        start = 0
        end = len(string)
        while string[start] in (" ", "\n"):
            start = start + 1
        while string[end - 1] in (" ", "\n"):
            end = end - 1

        return string[start:end]
    else:
        return ""


def make_title(string):
    string = remove_spaces(string)
    if string.upper() == string:
        return string
    else:
        return titlecase(string)


def handle_input(strings):
    if not strings:
        return None
    else:
        return [make_title(string) for string in strings.replace("/", ", ").split(", ")]


def handle_genres(genres):
    if not genres:
        return None
    else:
        genres = handle_input(genres)
        for genre in genres:
            if genre in metal_genres:
                genre = genre + " Metal"

        return genres


def handle_genre_categories(genre_categories):
    if not genre_categories:
        return None
    else:
        genre_categories = handle_input(genre_categories)
        return [
            genre_categories_dict[genre_category]
            if genre_category in genre_categories_dict
            else genre_category
            for genre_category in genre_categories
        ]


def handle_length(length):
    length = remove_spaces(length)
    if length == "Live":
        return "Live Album"
    elif length == "Other":
        return "Other Release"
    elif length == "Deluxe":
        return "Deluxe Edition"
    elif length == "Greatest Hits":
        return "Greatest Hits Album"
    elif length == "Cover":
        return "Cover Album"
    elif length == "Covers":
        return "Cover Album"
    elif length == "Covers Album":
        return "Cover Album"
    elif length == "Anniversary":
        return "Anniversary Edition"
    elif length == "Unreleased":
        return "Unreleased Album"
    else:
        return length
