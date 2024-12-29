from ...mode_switch import mode_setup
from ...utils import get_and_verify_env

gsa = mode_setup()

QOTD_WKS = gsa.open_by_url(get_and_verify_env("QOTD_SHEET_URL")).sheet1

QOTD_CHANNEL = int(get_and_verify_env("QOTD_CHANNEL"))
QOTD_APPROVAL_CHANNEL = int(get_and_verify_env("QOTD_APPROVAL_CHANNEL"))

QOTD_HOUR = 6
QOTD_MINUTE = 0

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))
