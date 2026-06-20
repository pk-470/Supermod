"""Smoke tests: prove pure feature modules import with no network at import time."""


def test_album_imports():
    from supermod.album_classes.album import Album

    album = Album(
        artist="some artist",
        title="some album",
        genres="Rock",
        release_date="2020-01-01",
    )
    assert album.artist == "Some Artist"


def test_feature_utils_imports_without_gspread():
    # If the env-based _constants or the lazy worksheet accessors regressed to
    # network-on-import, importing feature code would call gspread.open_by_url
    # and blow up here.
    from supermod.features.newsletter import _utils

    assert _utils is not None
    assert hasattr(_utils, "news_get")
