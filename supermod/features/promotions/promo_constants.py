from ...mode_switch import mode_setup
from ...utils import get_and_verify_env

gsa = mode_setup()

PROMOS_WKS = gsa.open_by_url(get_and_verify_env("QOTD_SHEET_URL")).get_worksheet(1)

SERVER = int(get_and_verify_env("SERVER"))
PROMOS_CHANNEL = int(get_and_verify_env("PROMOS_CHANNEL"))
REJECTED_PROMOS_CHANNEL = int(get_and_verify_env("QOTD_APPROVAL_CHANNEL"))

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))
