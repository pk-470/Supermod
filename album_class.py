# Flag emoji archive
from discord_country_flags import discord_country_flags


class album:
    def __init__(
        self,
        artists,
        title,
        genres,
        release_date=None,
        countries=None,
        length=None,
        FFO=None,
    ):
        self.artists = handle_input(artists)
        self.title = remove_space(title)
        self.genres = handle_input(genres)
        self.length = handle_length(length)
        self.release_date = remove_space(release_date)
        self.countries = handle_input(countries)
        self.FFO = handle_input(FFO)

    def news_format(self):
        return (
            "  ".join([discord_country_flags[country] for country in self.countries])
            + "  | "
            + ", ".join(self.artists)
            + " - '"
            + self.title
            + "' (Genre: "
            + ", ".join(self.genres)
            + ")"
        )


def remove_space(string):
    if string and string[-1] == " ":
        string = string[:-1]
    return string


def handle_input(strings):
    return [remove_space(string) for string in strings.split(", ")]


def handle_length(length):
    length = remove_space(length)
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
