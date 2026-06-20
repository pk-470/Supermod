"""Smoke tests: prove pure modules import and the fake-_constants trick works."""


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
    # If conftest's fake _constants registration failed, importing feature
    # code would run gspread.open_by_url and blow up here.
    from supermod.features.newsletter import _utils

    assert _utils is not None
    assert hasattr(_utils, "news_get")
