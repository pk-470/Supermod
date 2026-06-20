from functools import lru_cache

import gspread

from supermod._paths import LOCAL_MARKER, TOKENS_PATH
from supermod._utils import get_and_verify_env


@lru_cache(maxsize=1)
def is_local() -> bool:
    """
    Return True in local development, detected by a gitignored .local marker
    file at the project root (so deployment is always in production mode).
    """
    return LOCAL_MARKER.exists()


@lru_cache(maxsize=1)
def load_local_env() -> None:
    """
    In local mode, load secrets from .tokens/.env into the environment once;
    a no-op in deployment, where configuration comes from real env variables.
    """
    if is_local():
        from dotenv import load_dotenv

        load_dotenv(str(TOKENS_PATH / ".env"))


@lru_cache(maxsize=1)
def mode_setup():
    """Authenticate with Google Sheets for the current run mode and return the client."""
    load_local_env()

    if is_local():
        gsa = gspread.service_account(str(TOKENS_PATH / "service_account.json"))
    else:
        from json import loads

        gsa = gspread.service_account_from_dict(
            loads(get_and_verify_env("SERVICE_ACCOUNT_CRED"))
        )

    return gsa
