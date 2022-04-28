# Titlecase
from titlecase import titlecase

# Flag emoji archive
from data.discord_country_flags import discord_country_flags


class Album:
    def __init__(
        self,
        artist,
        title,
        genres=None,
        release_date=None,
        countries=None,
        length=None,
        ffo=None,
    ):
        self.artist = remove_spaces(artist)
        self.title = remove_spaces(title)
        self.genres = handle_input(genres)
        self.length = handle_length(length)
        self.release_date = remove_spaces(release_date)
        self.countries = handle_input(countries)
        self.ffo = handle_input(ffo)

    def news_format(self):
        try:
            return (
                "  ".join(
                    [discord_country_flags[country] for country in self.countries]
                )
                + f"  | {self.artist} - '{self.title}' (Genre: "
                + ", ".join(self.genres)
                + ")"
            )
        except:
            print(
                f"Something went wrong with album {self.title} by {self.artist} "
                f"from {self.countries} (Genre: {self.genres}, "
                f"Release date: {self.release_date})."
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

        string = string[start:end]
        if string.upper() == string:
            return string
        else:
            return titlecase(string)
    else:
        return ""


def handle_input(strings):
    if strings == None:
        return strings
    else:
        return [
            remove_spaces(string) for string in strings.replace("/", ", ").split(", ")
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
