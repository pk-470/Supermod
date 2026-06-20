from functools import lru_cache

from supermod._mode_setup import load_local_env, mode_setup
from supermod._utils import get_and_verify_env

load_local_env()

SERVER = int(get_and_verify_env("SERVER"))
PROMOS_CHANNEL = int(get_and_verify_env("PROMOS_CHANNEL"))
REJECTED_PROMOS_CHANNEL = int(get_and_verify_env("QOTD_APPROVAL_CHANNEL"))

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))


@lru_cache(maxsize=1)
def promos_wks():
    """Lazily open and memoize the promotions worksheet (second tab)."""
    return mode_setup().open_by_url(get_and_verify_env("QOTD_SHEET_URL")).get_worksheet(1)
