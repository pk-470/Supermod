from album_classes.classes_utils import *


class Album:
    def __init__(
        self,
        artist,
        title,
        genres,
        release_date,
    ):
        self.artist = make_title(artist)
        self.title = make_title(title)
        self.genres = handle_genres(genres)
        self.release_date = remove_spaces(release_date)
