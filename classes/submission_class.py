# Parent album class
from classes.album_class import album, remove_spaces

# Library to create urls
import urllib.parse as url


class submission(album):
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
    ):
        album.__init__(
            self,
            artist,
            title,
            genres,
            release_date,
            countries=None,
            length=None,
            FFO=None,
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
        self.link = "https://www.google.com/search?q=" + url.quote_plus(
            self.artist + " " + self.title
        )

    def masterlist_format_no_mention(self):
        return (
            self.title
            + " by "
            + self.artist
            + " ("
            + self.release_date
            + ") ("
            + ", ".join(self.genres)
            + ")"
        )

    def masterlist_format(self):
        return (
            self.masterlist_format_no_mention() + " <@!" + str(self.submitter_id) + ">"
        )

    def sub_check_msg_full(self):
        return (
            "Album: **"
            + self.masterlist_format_no_mention()
            + "**, submitted by **"
            + self.submitter_name
            + "** ("
            + str(self.submitter_id)
            + "), request: **"
            + str(self.request)
            + "** in **"
            + self.masterlist.upper()
            + "**, link: "
            + self.link
        )

    def swap(self, attribute_1, attrubute_2):
        if {attribute_1, attrubute_2} == {"artist", "title"}:
            self.title, self.artist = self.artist, self.title
        elif {attribute_1, attrubute_2} == {"year", "genre"}:
            self.genres, self.release_date = self.release_date, self.genres


class sub_error:
    def __init__(self, message):
        self.message = message
