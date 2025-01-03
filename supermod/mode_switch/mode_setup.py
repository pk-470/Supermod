# pylint: disable=redefined-outer-name,import-outside-toplevel

import gspread

from ..paths import MODE_SWITCH_PATH, TOKENS_PATH
from ..utils import get_and_verify_env

with open(MODE_SWITCH_PATH, "r", encoding="utf-8") as f:
    LOCAL_MODE = f.read()


def mode_setup():
    """
    Import data according to LOCAL_MODE status.
    """
    with open(MODE_SWITCH_PATH, "r", encoding="utf-8") as f:
        LOCAL_MODE = f.read()

    if LOCAL_MODE == "ON":

        from dotenv import load_dotenv

        load_dotenv(f"{TOKENS_PATH}/.env")

        gsa = gspread.service_account(f"{TOKENS_PATH}/service_account.json")  # type: ignore[reportPrivateImportUsage]

    else:

        from json import loads

        gsa = gspread.service_account_from_dict(  # type: ignore[reportPrivateImportUsage]
            loads(get_and_verify_env("SERVICE_ACCOUNT_CRED"))
        )

    return gsa
