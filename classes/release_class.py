# Parent Album class
from classes.album_class import *

# Flag emoji archive
from data.discord_country_flags import discord_country_flags


class Release(Album):
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
