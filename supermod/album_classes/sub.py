import urllib.parse as url
from typing import Optional

from discord import Message

from .album import Album


class Sub(Album):
    def __init__(
        self,
        artist: str,
        title: str,
        genres: str,
        release_date: str,
        submitter_name: str,
        submitter_id: int,
        masterlist: str,
        message: Optional[Message] = None,
        request: Optional[str] = None,
        warning: Optional[str] = None,
    ):
        Album.__init__(
            self,
            artist,
            title,
            genres,
            release_date,
        )
        self.submitter_name = submitter_name
        self.submitter_id = submitter_id
        self.masterlist = masterlist.strip().lower()
        self.message = message
        self.request = request
        self.warning = warning
        self.link = "https://www.google.com/search?q=" + url.quote_plus(
            f"{self.artist} {self.title}"
        )

    def masterlist_format_no_mention(self):
        return (
            f"{self.title} _by_ {self.artist} ({self.release_date}) ("
            + ", ".join(self.genres)
            + ")"
        )

    def masterlist_format(self):
        return self.masterlist_format_no_mention() + f" <@!{self.submitter_id}>"

    def sub_check_msg_full(self):
        return (
            f"Album: **{self.masterlist_format_no_mention()}**, "
            + f"submitted by **{self.submitter_name}** ({self.submitter_id}), "
            + f"request: **{self.request}** in **{self.masterlist.upper()}**, "
            + f"link: {self.link}"
        )


class SubError:
    def __init__(self, message: Message):
        self.message = message
