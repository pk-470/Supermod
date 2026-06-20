from supermod._mode_setup import load_local_env
from supermod._utils import get_and_verify_env

load_local_env()

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))
