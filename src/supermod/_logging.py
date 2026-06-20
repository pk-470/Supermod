import logging
import sys

import pendulum

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S %Z"

_configured = False


class TorontoFormatter(logging.Formatter):
    """Format record timestamps in America/Toronto with a DST-aware %Z abbreviation."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return pendulum.from_timestamp(record.created, tz="America/Toronto").strftime(
            datefmt or _DATE_FORMAT
        )


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger with a single stdout handler (idempotent), and
    quieten the chatty discord and gspread libraries to WARNING.
    """
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(TorontoFormatter(_FORMAT, _DATE_FORMAT))

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)

    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("gspread").setLevel(logging.WARNING)
    # discord.py transparently retries rate limits (429); its per-request WARNING
    # spam during bulk ops (e.g. masterlist purges of >14-day-old messages) is not
    # actionable, so keep only genuine http errors.
    logging.getLogger("discord.http").setLevel(logging.ERROR)

    _configured = True
