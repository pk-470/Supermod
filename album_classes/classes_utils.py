from titlecase import titlecase
from data.genres import *


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


def handle_genre_categories(genre_categories):
    if genre_categories is None:
        return None
    else:
        genre_categories = handle_input(genre_categories)
        return [
            genre_categories_dict[genre_category]
            if genre_category in genre_categories_dict
            else genre_category
            for genre_category in genre_categories
        ]
