from ...mode_switch import mode_setup
from ...utils import get_and_verify_env

gsa = mode_setup()

NEWS_SHEET = gsa.open_by_url(get_and_verify_env("NEWS_SHEET_URL"))

GENRE_CHANNELS = {
    "Experimental Rock": int(get_and_verify_env("EXPERIMENTAL_ROCK")),
    "Hard Rock": int(get_and_verify_env("HARD_ROCK")),
    "Soft Rock": int(get_and_verify_env("SOFT_ROCK")),
    "Punk": int(get_and_verify_env("PUNK")),
    "Core": int(get_and_verify_env("CORE")),
    "Metal": int(get_and_verify_env("METAL")),
    "Extreme Metal": int(get_and_verify_env("EXTREME_METAL")),
    "Classical / Jazz / Blues": int(get_and_verify_env("CLASSICAL_JAZZ_BLUES")),
    "Country / Folk": int(get_and_verify_env("COUNTRY_FOLK")),
    "Electronic": int(get_and_verify_env("ELECTRONIC")),
    "Pop / Hip Hop": int(get_and_verify_env("POP_HIP_HOP")),
}

STAFF_ROLE = int(get_and_verify_env("STAFF_ROLE"))
