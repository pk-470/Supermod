from album_classes.album import Album
from album_classes.classes_utils import *
from data.discord_country_flags import discord_country_flags


class Release(Album):
    def __init__(
        self,
        artist,
        title,
        genres,
        release_date,
        length=None,
        countries=None,
        ffo=None,
        genre_categories=None,
    ):
        Album.__init__(
            self,
            artist,
            title,
            genres,
            release_date,
        )
        self.length = handle_length(length)
        self.countries = handle_input(countries)
        self.ffo = handle_input(ffo)
        self.genre_categories = handle_genre_categories(genre_categories)

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
            return (
                f"**ERROR:** Something went wrong with album {self.title} by "
                f"{self.artist} from {self.countries} (Genre: {self.genres}, "
                f"Release date: {self.release_date})."
            )
