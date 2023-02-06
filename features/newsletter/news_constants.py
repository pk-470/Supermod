from os import getenv
from mode_switch import mode_setup

gsa = mode_setup()

NEWS_SHEET = gsa.open_by_url(getenv("NEWS_SHEET_URL"))

GENRE_CHANNELS = {
    "Experimental Rock": int(getenv("EXPERIMENTAL_ROCK")),
    "Hard Rock": int(getenv("HARD_ROCK")),
    "Soft Rock": int(getenv("SOFT_ROCK")),
    "Punk": int(getenv("PUNK")),
    "Core": int(getenv("CORE")),
    "Metal": int(getenv("METAL")),
    "Extreme Metal": int(getenv("EXTREME_METAL")),
    "Classical / Jazz / Blues": int(getenv("CLASSICAL_JAZZ_BLUES")),
    "Country / Folk": int(getenv("COUNTRY_FOLK")),
    "Electronic": int(getenv("ELECTRONIC")),
    "Pop / Hip Hop": int(getenv("POP_HIP_HOP")),
}

STAFF_ROLE = int(getenv("STAFF_ROLE"))
