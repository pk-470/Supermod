from ...mode_switch import mode_setup
from ...utils import get_and_verify_env

mode_setup()

ANNOUNCEMENTS_CHANNEL = int(get_and_verify_env("ANNOUNCEMENTS_CHANNEL"))
SUBMISSIONS_CHANNEL = int(get_and_verify_env("SUBMISSIONS_CHANNEL"))
VOTED_CHANNEL = int(get_and_verify_env("VOTED_CHANNEL"))
TALK_TO_THE_STAFF_CHANNEL = int(get_and_verify_env("TALK_TO_THE_STAFF_CHANNEL"))

LISTENERS_ROLE_MENTION = "<@&" + str(get_and_verify_env("LISTENERS_ROLE")) + ">"

SUBMISSIONS_OPEN_DAY = "Sunday"
SUBMISSIONS_OPEN_HOUR = 0
SUBMISSIONS_OPEN_MINUTE = 0
SUBMISSIONS_CLOSED_DAY = "Thursday"
SUBMISSIONS_CLOSED_HOUR = 0
SUBMISSIONS_CLOSED_MINUTE = 0
