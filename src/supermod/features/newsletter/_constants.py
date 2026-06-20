from functools import lru_cache

from supermod._mode_setup import load_local_env, mode_setup
from supermod._utils import get_and_verify_env

load_local_env()

GENRE_CHANNELS = {
    "Experimental Rock": int(get_and_verify_env("EXPERIMENTAL_ROCK")),
    "Hard Rock": int(get_and_verify_env("HARD_ROCK")),
    "Soft Rock": int(get_and_verify_env("SOFT_ROCK")),
    "Punk": int(get_and_verify_env("PUNK")),
    "Core": int(get_and_verify_env("CORE")),
    "Metal": int(get_and_verify_env("METAL")),
    "Extreme Metal": int(get_and_verify_env("EXTREME_METAL")),
    "Classical / Jazz / Blues": int(get_and_verify_env("CLASSICAL_JAZZ_BLUES")),
    "Country / Folk": int(get_and_verify_env("COUNTRY_FOLK")),
    "Electronic": int(get_and_verify_env("ELECTRONIC")),
    "Pop / Hip Hop": int(get_and_verify_env("POP_HIP_HOP")),
}

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))


@lru_cache(maxsize=1)
def news_sheet():
    """Lazily open and memoize the newsletter spreadsheet."""
    return mode_setup().open_by_url(get_and_verify_env("NEWS_SHEET_URL"))
