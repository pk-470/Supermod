# Parent Album class
from classes.album_class import *

# Library to create urls
import urllib.parse as url


class Submission(Album):
    def __init__(
        self,
        artist,
        title,
        genres,
        release_date,
        submitter_name,
        submitter_id,
        masterlist,
        message,
        request=None,
        warning=None,
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
        self.masterlist = remove_spaces(masterlist).lower()
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
            f"submitted by **{self.submitter_name}** ({self.submitter_id}), "
            f"request: **{self.request}** in **{self.masterlist.upper()}**, "
            f"link: {self.link}"
        )


class Sub_error:
    def __init__(self, message):
        self.message = message
