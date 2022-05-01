# Parent album class
from classes.album_class import Album, remove_spaces

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
            genre_categories=None,
            countries=None,
            length=None,
            ffo=None,
        )
        self.submitter_name = submitter_name
        self.submitter_id = submitter_id
        masterlist = remove_spaces(masterlist).lower()
        try:
            if masterlist.startswith("voted"):
                self.masterlist = "voted"
            elif masterlist.startswith("new"):
                self.masterlist = "new"
            elif masterlist.startswith("modern"):
                self.masterlist = "modern"
            elif masterlist.startswith("classic"):
                self.masterlist = "classic"
            elif masterlist.startswith("theme"):
                self.masterlist = "theme"
            else:
                self.masterlist = "wrong/missing"
        except:
            self.masterlist = "wrong/missing"
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
