from os import getenv

import pendulum


def print_info(message: object):
    print(
        f"{pendulum.now('America/Toronto').strftime('%Y-%m-%d %H:%M:%S EST')}: {message}"
    )


def get_and_verify_env(var_name: str) -> str:
    var = getenv(var_name)
    assert var is not None, f"Environment variable {var_name} is not found"
    return var
