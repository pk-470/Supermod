from functools import lru_cache

from supermod._mode_setup import load_local_env, mode_setup
from supermod._utils import get_and_verify_env

load_local_env()

QOTD_CHANNEL = int(get_and_verify_env("QOTD_CHANNEL"))
QOTD_APPROVAL_CHANNEL = int(get_and_verify_env("QOTD_APPROVAL_CHANNEL"))

QOTD_HOUR = 6
QOTD_MINUTE = 0

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))


@lru_cache(maxsize=1)
def qotd_wks():
    """Lazily open and memoize the QOTD worksheet."""
    return mode_setup().open_by_url(get_and_verify_env("QOTD_SHEET_URL")).sheet1
