from ...mode_switch import mode_setup
from ...utils import get_and_verify_env

gsa = mode_setup()

ALBUMS_WKS = gsa.open_by_url(get_and_verify_env("ALBUMS_SHEET_URL")).sheet1
WEEKS_WKS = gsa.open_by_url(get_and_verify_env("ALBUMS_SHEET_URL")).get_worksheet(1)
SUBS_SHEET = gsa.open_by_url(get_and_verify_env("SUBS_SHEET_URL"))

SUB_APPROVAL_CHANNEL = int(get_and_verify_env("QOTD_APPROVAL_CHANNEL"))

SUBMISSIONS_CHANNEL = int(get_and_verify_env("SUBMISSIONS_CHANNEL"))
VOTED_CHANNEL = int(get_and_verify_env("VOTED_CHANNEL"))
NEW_CHANNEL = int(get_and_verify_env("NEW_CHANNEL"))
MODERN_CHANNEL = int(get_and_verify_env("MODERN_CHANNEL"))
CLASSIC_CHANNEL = int(get_and_verify_env("CLASSIC_CHANNEL"))
THEME_CHANNEL = int(get_and_verify_env("THEME_CHANNEL"))
ANYTHING_CHANNEL = int(get_and_verify_env("ANYTHING_CHANNEL"))

MASTERLIST_CHANNEL_DICT = {
    "voted": VOTED_CHANNEL,
    "new": NEW_CHANNEL,
    "modern": MODERN_CHANNEL,
    "classic": CLASSIC_CHANNEL,
    "theme": THEME_CHANNEL,
    "anything": ANYTHING_CHANNEL,
}

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))
