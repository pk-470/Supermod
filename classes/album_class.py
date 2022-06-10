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
    ):
        self.artist = make_title(artist)
        self.title = make_title(title)
        self.genres = handle_genres(genres)
        self.release_date = remove_spaces(release_date)


def remove_spaces(string):
    if string is None:
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
    if strings is None:
        return None
    else:
        return [make_title(string) for string in strings.replace("/", ", ").split(", ")]


def handle_genres(genres):
    if genres is None:
        return None
    else:
        genres = handle_input(genres)
        for genre in genres:
            if genre in metal_genres:
                genre = genre + " Metal"

        return genres


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
