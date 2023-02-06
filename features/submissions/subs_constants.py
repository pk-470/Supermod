from os import getenv
from mode_switch import mode_setup

gsa = mode_setup()

ALBUMS_WKS = gsa.open_by_url(getenv("ALBUMS_SHEET_URL")).sheet1
WEEKS_WKS = gsa.open_by_url(getenv("ALBUMS_SHEET_URL")).get_worksheet(1)
SUBS_SHEET = gsa.open_by_url(getenv("SUBS_SHEET_URL"))

SUB_APPROVAL_CHANNEL = int(getenv("QOTD_APPROVAL_CHANNEL"))

SUBMISSIONS_CHANNEL = int(getenv("SUBMISSIONS_CHANNEL"))
VOTED_CHANNEL = int(getenv("VOTED_CHANNEL"))
NEW_CHANNEL = int(getenv("NEW_CHANNEL"))
MODERN_CHANNEL = int(getenv("MODERN_CHANNEL"))
CLASSIC_CHANNEL = int(getenv("CLASSIC_CHANNEL"))
THEME_CHANNEL = int(getenv("THEME_CHANNEL"))

MASTERLIST_CHANNEL_DICT = {
    "voted": VOTED_CHANNEL,
    "new": NEW_CHANNEL,
    "modern": MODERN_CHANNEL,
    "classic": CLASSIC_CHANNEL,
    "theme": THEME_CHANNEL,
}

STAFF_ROLE = int(getenv("STAFF_ROLE"))
