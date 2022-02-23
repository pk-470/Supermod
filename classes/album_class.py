# Flag emoji archive
from data.discord_country_flags import discord_country_flags


class album:
    def __init__(
        self,
        artist,
        title,
        genres=None,
        release_date=None,
        countries=None,
        length=None,
        FFO=None,
    ):
        self.artist = remove_spaces(artist)
        self.title = remove_spaces(title)
        self.genres = handle_input(genres)
        self.length = handle_length(length)
        self.release_date = remove_spaces(release_date)
        self.countries = handle_input(countries)
        self.FFO = handle_input(FFO)

    def news_format(self):
        try:
            return (
                "  ".join(
                    [discord_country_flags[country] for country in self.countries]
                )
                + "  | "
                + self.artist
                + " - '"
                + self.title
                + "' (Genre: "
                + ", ".join(self.genres)
                + ")"
            )
        except:
            print(
                "Something went wrong with album "
                + self.title
                + " by "
                + self.artist
                + " from "
                + str(self.countries)
                + " (Genre: "
                + str(self.genres)
                + ", Release date: "
                + str(self.release_date)
                + " )."
            )
            return ""


def remove_spaces(string):
    if string == None:
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


def handle_input(strings):
    if strings == None:
        return strings
    else:
        return [remove_spaces(string) for string in strings.split(", ")]


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
