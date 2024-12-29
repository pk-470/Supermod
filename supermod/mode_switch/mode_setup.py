from os import getenv

import gspread

from ..paths import MODE_SWITCH_PATH, TOKENS_PATH
from ..utils import get_and_verify_env

LOCAL_MODE = open(MODE_SWITCH_PATH, "r").read()


def mode_setup():
    """
    Import data according to LOCAL_MODE status.
    """
    LOCAL_MODE = open(MODE_SWITCH_PATH, "r").read()

    if LOCAL_MODE == "ON":

        from dotenv import load_dotenv

        load_dotenv(f"{TOKENS_PATH}/.env")

        gsa = gspread.service_account(f"{TOKENS_PATH}/service_account.json")

    elif LOCAL_MODE == "OFF":

        from json import loads

        gsa = gspread.service_account_from_dict(
            loads(get_and_verify_env("SERVICE_ACCOUNT_CRED"))
        )

    return gsa
