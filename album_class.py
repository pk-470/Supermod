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
        self.length = remove_space(length)
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
