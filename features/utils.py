import pendulum


def print_info(message: str):
    print(
        f"{pendulum.now('America/Toronto').strftime('%Y-%m-%d %H:%M:%S EST')}: {message}"
    )
