from ...mode_switch import mode_setup
from ...utils import get_and_verify_env

gsa = mode_setup()

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))
