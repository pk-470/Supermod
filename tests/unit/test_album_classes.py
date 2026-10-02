"""Unit tests for supermod.album_classes (album.py, release.py, sub.py)."""

import urllib.parse as url
from typing import Any

import pytest

from supermod.album_classes.album import Album
from supermod.album_classes.release import Release
from supermod.album_classes.sub import Sub

# --------------------------------------------------------------------------- #
# Album.make_title
# --------------------------------------------------------------------------- #


def test_make_title_titlecases_mixed_case():
    assert Album.make_title("the dark side of the moon") == "The Dark Side of the Moon"


def test_make_title_preserves_all_caps():
    # An all-caps string is intentional styling -> left untouched.
    assert Album.make_title("USA") == "USA"
    assert Album.make_title("MGMT") == "MGMT"


def test_make_title_strips_whitespace():
    assert Album.make_title("  opeth  ") == "Opeth"


# --------------------------------------------------------------------------- #
# Album.handle_input
# --------------------------------------------------------------------------- #


def test_handle_input_comma_split_and_titlecase():
    assert Album.handle_input("death, power") == ["Death", "Power"]


def test_handle_input_slash_split():
    # "/" is normalized to ", " before splitting.
    assert Album.handle_input("death/power") == ["Death", "Power"]


def test_handle_input_empty_returns_empty_list():
    assert Album.handle_input("") == []


def test_handle_input_whitespace_returns_empty_list():
    assert Album.handle_input("   ") == []


def test_handle_input_drops_empty_items():
    assert Album.handle_input("Rock, ") == ["Rock"]


# --------------------------------------------------------------------------- #
# Album.handle_genres
# --------------------------------------------------------------------------- #


def test_handle_genres_appends_metal_suffix():
    # "Death" is in METAL_GENRES -> becomes "Death Metal"; "Pop" is not.
    assert Album.handle_genres("Death, Pop") == ["Death Metal", "Pop"]


def test_handle_genres_slash_split_with_metal_suffix():
    assert Album.handle_genres("Death/Power") == ["Death Metal", "Power Metal"]


def test_handle_genres_mixed_split_and_suffix():
    assert Album.handle_genres("Death/Power, Pop") == [
        "Death Metal",
        "Power Metal",
        "Pop",
    ]


# --------------------------------------------------------------------------- #
# Album.handle_length
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Live", "Live Album"),
        ("Other", "Other Release"),
        ("Deluxe", "Deluxe Edition"),
        ("Greatest Hits", "Greatest Hits Album"),
        ("Cover", "Cover Album"),
        ("Covers", "Cover Album"),
        ("Covers Album", "Cover Album"),
        ("Anniversary", "Anniversary Edition"),
        ("Unreleased", "Unreleased Album"),
    ],
)
def test_handle_length_aliases(raw, expected):
    assert Album.handle_length(raw) == expected


def test_handle_length_passthrough_and_strip():
    # Unknown values are returned stripped, unchanged.
    assert Album.handle_length("  EP  ") == "EP"


# --------------------------------------------------------------------------- #
# Sub
# --------------------------------------------------------------------------- #


def _make_sub(**overrides):
    kwargs: dict[str, Any] = dict(
        artist="opeth",
        title="blackwater park",
        genres="Death, Progressive",
        release_date="2001-03-12",
        submitter_name="tester",
        submitter_id=42,
        masterlist="  Voted  ",
    )
    kwargs.update(overrides)
    return Sub(**kwargs)


def test_sub_masterlist_lowercased_and_stripped():
    sub = _make_sub(masterlist="  Voted  ")
    assert sub.masterlist == "voted"


def test_sub_masterlist_format_no_mention_exact():
    sub = _make_sub()
    # ordering: title _by_ artist (release_date) (genres)
    assert (
        sub.masterlist_format_no_mention()
        == "Blackwater Park _by_ Opeth (2001-03-12) (Death Metal, Progressive)"
    )


def test_sub_masterlist_format_exact_with_mention():
    sub = _make_sub(submitter_id=42)
    assert (
        sub.masterlist_format()
        == "Blackwater Park _by_ Opeth (2001-03-12) (Death Metal, Progressive) <@!42>"
    )


def test_sub_link_url_encoding():
    sub = _make_sub()
    expected = "https://www.google.com/search?q=" + url.quote_plus(
        "Opeth Blackwater Park"
    )
    assert sub.link == expected
    # sanity: spaces encoded as '+', not raw spaces
    assert " " not in sub.link
    assert sub.link.endswith("Opeth+Blackwater+Park")


# --------------------------------------------------------------------------- #
# Release.news_format
# --------------------------------------------------------------------------- #


def test_news_format_known_country():
    rel = Release(
        artist="opeth",
        title="blackwater park",
        genres="Death, Progressive",
        release_date="2001-03-12",
        countries="Sweden",
    )
    assert (
        rel.news_format()
        == ":flag_se:  | Opeth - 'Blackwater Park' (Genre: Death Metal, Progressive)"
    )


def test_news_format_blank_country_is_reported_as_error():
    # A release with no country is reported to staff instead of being posted.
    rel = Release(
        artist="foo",
        title="bar",
        genres="Rock",
        release_date="2020",
        countries="",
    )
    assert rel.news_format().startswith("**ERROR:**")


def test_news_format_unknown_country_is_reported_as_error():
    # An unrecognised country (often a typo) is reported to staff instead of
    # being posted without its flag.
    rel = Release(
        artist="foo",
        title="bar",
        genres="Rock",
        release_date="2020",
        countries="Atlantis",
    )
    assert rel.news_format().startswith("**ERROR:**")


@pytest.mark.parametrize(
    ("country", "flag"),
    [
        ("US", ":flag_us:"),
        ("Bosnia", ":flag_ba:"),
        ("Turkiye", ":flag_tr:"),
        ("Czechia", ":flag_cz:"),
    ],
)
def test_news_format_alternative_country_names(country, flag):
    # Alternative names seen in the newsletter sheet.
    rel = Release(
        artist="foo",
        title="bar",
        genres="Rock",
        release_date="2020",
        countries=country,
    )
    assert rel.news_format().startswith(f"{flag}  | ")
