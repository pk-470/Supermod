from titlecase import titlecase

from ..data.genres import *


class Album:
    def __init__(
        self,
        artist: str,
        title: str,
        genres: str,
        release_date: str,
    ):
        self.artist = self.make_title(artist)
        self.title = self.make_title(title)
        self.genres = self.handle_genres(genres)
        self.release_date = release_date.strip()

    @classmethod
    def make_title(cls, string: str) -> str:
        string = string.strip()
        if string.upper() == string:
            return string
        return titlecase(string)

    @classmethod
    def handle_input(cls, strings: str) -> list[str]:
        return [
            cls.make_title(string) for string in strings.replace("/", ", ").split(", ")
        ]

    @classmethod
    def handle_genres(cls, genres: str) -> list[str]:
        genres_list = [
            genre + " Metal" if genre in METAL_GENRES else genre
            for genre in cls.handle_input(genres)
        ]
        return genres_list

    @classmethod
    def handle_length(cls, length: str) -> str:
        length = length.strip()
        if length == "Live":
            return "Live Album"
        if length == "Other":
            return "Other Release"
        if length == "Deluxe":
            return "Deluxe Edition"
        if length == "Greatest Hits":
            return "Greatest Hits Album"
        if length == "Cover":
            return "Cover Album"
        if length == "Covers":
            return "Cover Album"
        if length == "Covers Album":
            return "Cover Album"
        if length == "Anniversary":
            return "Anniversary Edition"
        if length == "Unreleased":
            return "Unreleased Album"
        return length
