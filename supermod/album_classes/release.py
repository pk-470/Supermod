from typing import Optional

from ..data.discord_country_flags import DISCORD_COUNTRY_FLAGS
from ..data.genres import GENRE_CATEGORIES
from ..utils import print_info
from .album import Album


class Release(Album):
    def __init__(
        self,
        artist: str,
        title: str,
        genres: str,
        release_date: str,
        length: Optional[str] = None,
        countries: Optional[str] = None,
        ffo: Optional[str] = None,
        genre_categories: Optional[str] = None,
    ):
        Album.__init__(
            self,
            artist,
            title,
            genres,
            release_date,
        )
        self.length = None if length is None else self.handle_length(length)
        self.countries = [] if countries is None else self.handle_input(countries)
        self.ffo = None if ffo is None else self.handle_input(ffo)
        self.genre_categories = (
            []
            if genre_categories is None
            else self.handle_genre_categories(genre_categories)
        )

    @classmethod
    def handle_genre_categories(cls, genre_categories: str) -> list[str]:
        return [
            (
                GENRE_CATEGORIES[genre_category]
                if genre_category in GENRE_CATEGORIES
                else genre_category
            )
            for genre_category in cls.handle_input(genre_categories)
        ]

    def news_format(self):
        try:
            return (
                "  ".join(
                    [DISCORD_COUNTRY_FLAGS[country] for country in self.countries]
                )
                + f"  | {self.artist} - '{self.title}' (Genre: "
                + ", ".join(self.genres)
                + ")"
            )
        except Exception as e:
            print_info(f"{type(e).__name__}: {e}")
            return (
                f"**ERROR:** Something went wrong with album {self.title} by "
                + f"{self.artist} from {self.countries} (Genre: {self.genres}, "
                + f"Release date: {self.release_date})."
            )
