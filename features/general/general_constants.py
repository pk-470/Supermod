from os import getenv
from mode_switch import mode_setup

gsa = mode_setup()

STAFF_ROLE = int(getenv("STAFF_ROLE"))
