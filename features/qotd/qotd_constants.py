from os import getenv
from mode_switch import mode_setup

gsa = mode_setup()

QOTD_WKS = gsa.open_by_url(getenv("QOTD_SHEET_URL")).sheet1

QOTD_CHANNEL = int(getenv("QOTD_CHANNEL"))
QOTD_APPROVAL_CHANNEL = int(getenv("QOTD_APPROVAL_CHANNEL"))

QOTD_HOUR = 6
QOTD_MINUTE = 0

STAFF_ROLE = int(getenv("STAFF_ROLE"))
