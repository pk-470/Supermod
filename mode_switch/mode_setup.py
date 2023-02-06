from os import getenv
import gspread


LOCAL_MODE = open("mode_switch/mode_switch.txt", "r").read()


def mode_setup():
    """
    Import data according to LOCAL_MODE status.
    """

    if LOCAL_MODE == "ON":

        from dotenv import load_dotenv

        load_dotenv("tokens/.env")

        gsa = gspread.service_account("tokens/service_account.json")

    elif LOCAL_MODE == "OFF":

        from json import loads

        gsa = gspread.service_account_from_dict(loads(getenv("SERVICE_ACCOUNT_CRED")))

    return gsa
