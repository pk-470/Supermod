from os import getenv
from mode_switch import mode_setup

gsa = mode_setup()

PROMOS_WKS = gsa.open_by_url(getenv("QOTD_SHEET_URL")).get_worksheet(1)

SERVER = int(getenv("SERVER"))
PROMOS_CHANNEL = int(getenv("PROMOS_CHANNEL"))
REJECTED_PROMOS_CHANNEL = int(getenv("QOTD_APPROVAL_CHANNEL"))

STAFF_ROLE = int(getenv("STAFF_ROLE"))
