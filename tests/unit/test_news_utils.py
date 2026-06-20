"""
Unit tests for ``supermod.features.newsletter._utils`` pure helpers: ``week_no``,
``end_of_week``, ``week_check``, ``ordinal``, ``plural``, ``day_trim`` and
``post_split``.
"""

from __future__ import annotations

import pendulum
import pytest

from supermod.features.newsletter._utils import (
    day_trim,
    end_of_week,
    ordinal,
    plural,
    post_split,
    week_check,
    week_no,
)

# --- week_no -----------------------------------------------------------------


def test_week_no_start_of_year_is_week_1():
    soy = pendulum.datetime(2026, 1, 1, tz="America/Toronto")
    assert week_no(soy) == 1


def test_week_no_day_6_still_week_1():
    soy = pendulum.datetime(2026, 1, 1, tz="America/Toronto")
    assert week_no(soy.add(days=6)) == 1


def test_week_no_day_7_rolls_to_week_2():
    soy = pendulum.datetime(2026, 1, 1, tz="America/Toronto")
    assert week_no(soy.add(days=7)) == 2


def test_week_no_day_13_still_week_2():
    soy = pendulum.datetime(2026, 1, 1, tz="America/Toronto")
    assert week_no(soy.add(days=13)) == 2


def test_week_no_day_14_rolls_to_week_3():
    soy = pendulum.datetime(2026, 1, 1, tz="America/Toronto")
    assert week_no(soy.add(days=14)) == 3


def test_week_no_frozen_now(frozen_now):
    # Wed 2026-06-17 -> 167 days into the year -> week 24.
    assert week_no(frozen_now) == 24


# --- end_of_week -------------------------------------------------------------


def test_end_of_week_returns_week_and_title_day(frozen_now):
    title_day, week = end_of_week(frozen_now)
    assert week == 24
    # title day == start_of_year + (7*week - 1) days == last day of that week.
    expected = frozen_now.start_of("year").add(days=7 * 24 - 1)
    assert title_day == expected


def test_end_of_week_week_1():
    soy = pendulum.datetime(2026, 1, 1, tz="America/Toronto")
    title_day, week = end_of_week(soy)
    assert week == 1
    # Week 1 ends 6 days after the start of the year.
    assert title_day == soy.add(days=6)


# --- week_check --------------------------------------------------------------


def test_week_check_matching_week_is_true(frozen_now):
    # 6/17/2026 falls in week 24, same as frozen_now.
    assert week_check("6/17/2026", 24) is True


def test_week_check_other_date_same_week_is_true():
    # 6/15/2026 is also week 24.
    assert week_check("6/15/2026", 24) is True


def test_week_check_wrong_week_is_false():
    assert week_check("1/1/2026", 24) is False


def test_week_check_first_of_year_is_week_1():
    assert week_check("1/1/2026", 1) is True


def test_week_check_unparseable_value_is_false():
    assert week_check("not-a-date", 1) is False


# --- ordinal -----------------------------------------------------------------


@pytest.mark.parametrize(
    "num,expected",
    [
        (1, "st"),
        (2, "nd"),
        (3, "rd"),
        (11, "th"),
        (12, "th"),
        (13, "th"),
        (21, "st"),
        (22, "nd"),
        (23, "rd"),
        (31, "st"),
    ],
)
def test_ordinal(num, expected):
    assert ordinal(num) == expected


# --- plural ------------------------------------------------------------------


@pytest.mark.parametrize(
    "word,expected",
    [
        ("bus", "buses"),  # ends in s
        ("box", "boxes"),  # ends in x
        ("buzz", "buzzes"),  # ends in z
        ("dish", "dishes"),  # ends in sh
        ("church", "churches"),  # ends in ch
    ],
)
def test_plural_es_endings(word, expected):
    assert plural(word) == expected


@pytest.mark.parametrize(
    "word,expected",
    [
        ("LP", "LPs"),
        ("EP", "EPs"),
        ("album", "albums"),
    ],
)
def test_plural_default_s(word, expected):
    assert plural(word) == expected


# --- day_trim ----------------------------------------------------------------


def test_day_trim_strips_leading_zero():
    assert day_trim("07") == "7"


def test_day_trim_keeps_two_digit_day():
    assert day_trim("17") == "17"


# --- post_split --------------------------------------------------------------


def test_post_split_short_input_returns_single_chunk():
    text = "short post"
    assert post_split(text, 2000) == [text]


def test_post_split_newline_branch_no_chunk_exceeds_limit():
    text = "a" * 50 + "\n" + "b" * 50
    chunks = post_split(text, 60)
    assert all(len(chunk) <= 60 for chunk in chunks)
    assert len(chunks) > 1


def test_post_split_punctuation_branch_no_chunk_exceeds_limit():
    # No newline in the window forces the ``.?!`` split branch.
    text = "a" * 40 + ". " + "b" * 40
    chunks = post_split(text, 50)
    assert all(len(chunk) <= 50 for chunk in chunks)
    assert len(chunks) > 1


def test_post_split_no_delimiter_no_chunk_exceeds_limit():
    # Degenerate input with neither newline nor sentence punctuation.
    text = "a" * 200
    chunks = post_split(text, 60)
    assert all(len(chunk) <= 60 for chunk in chunks)


def test_post_split_realistic_no_chunk_exceeds_limit():
    text = ("Some words here and there. " * 30 + "\n") * 5
    chunks = post_split(text, 100)
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert len(chunks) > 1


@pytest.mark.xfail(reason="Group C #13: post_split drops a char on the punctuation-split branch")
def test_post_split_punctuation_branch_reconstructs_input():
    # CORRECT behavior: joining the chunks should reproduce the original text.
    # The punctuation-split branch currently drops the character after the
    # ``.``/``?``/``!`` (here the space), so this fails until that bug is fixed.
    text = "a" * 40 + ". " + "b" * 40
    chunks = post_split(text, 50)
    assert "".join(chunks) == text
