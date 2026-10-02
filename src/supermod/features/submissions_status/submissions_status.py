import logging

import pendulum
from discord import AllowedMentions, Object
from discord.ext import tasks
from discord.ext.commands import Bot, Cog

from supermod._mode_setup import is_local
from supermod._utils import text_channel
from supermod.features.submissions_status._constants import *

logger = logging.getLogger(__name__)

# The bot-wide default blocks role pings; these announcements opt back in for
# the Listeners role only.
LISTENERS_PING = AllowedMentions(
    everyone=False, users=False, roles=[Object(id=LISTENERS_ROLE)]
)


def channel_mention(channel_id: int) -> str:
    """
    Mention a channel by id. Unlike resolving it first, this works for any
    channel type (forum, voice, etc.), which is all a link in a message needs.
    """
    return f"<#{channel_id}>"


class SubmissionsStatus(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        if is_local():
            logger.info("Submissions status loop will not start (local mode).")
        else:
            self.submissions_status.start()

    # Submissions status announcement loop
    @tasks.loop(minutes=1)
    async def submissions_status(self):
        try:
            time_now = pendulum.now("America/Toronto")
            if (
                time_now.strftime("%A") == SUBMISSIONS_OPEN_DAY
                and time_now.hour == SUBMISSIONS_OPEN_HOUR
                and time_now.minute == SUBMISSIONS_OPEN_MINUTE
            ):
                await self._announce(
                    "open",
                    f"Hello {LISTENERS_ROLE_MENTION}! "
                    + "Voting has closed and our new weekly picks are now available in the Albums Under Review category, "
                    + f"located below {channel_mention(OL_WEEKLY_PLAYLIST_CHANNEL)}."
                    + f" When you have listened to an album in full, head to {channel_mention(INPUT_RATINGS_HERE_CHANNEL)} "
                    + "and submit your score. "
                    + f"Check the {channel_mention(FAQS_CHANNEL)} and the individual channel descriptions, "
                    + f"or head to {channel_mention(TALK_TO_THE_STAFF_CHANNEL)} if you need further assistance.",
                    time_now,
                )
            if (
                time_now.strftime("%A") == SUBMISSIONS_CLOSED_DAY
                and time_now.hour == SUBMISSIONS_CLOSED_HOUR
                and time_now.minute == SUBMISSIONS_CLOSED_MINUTE
            ):
                await self._announce(
                    "closed",
                    f"Hello {LISTENERS_ROLE_MENTION}! "
                    + f"{channel_mention(SUBMISSIONS_CHANNEL)} is now closed and voting is open. "
                    + f"Head to {channel_mention(VOTED_CHANNEL)} where you can vote up to 5 albums "
                    + "using the :thumbsup: emoji. The winning album will be revealed along with the random picks "
                    + "during the upcoming weekend and will be reviewed next week.",
                    time_now,
                )
        except Exception:
            logger.exception("Submissions status loop encountered an error.")
            return

    async def _announce(
        self, status: str, message: str, time_now: pendulum.DateTime
    ) -> None:
        announcements_channel = text_channel(self.bot, ANNOUNCEMENTS_CHANNEL)
        if announcements_channel is None:
            logger.error(
                "Submissions status loop: announcements channel %s could not be "
                "resolved; the '%s' announcement was not posted.",
                ANNOUNCEMENTS_CHANNEL,
                status,
            )
            return
        await announcements_channel.send(message, allowed_mentions=LISTENERS_PING)
        logger.info(
            "'Submissions is %s' message has been posted (date: %s).",
            status,
            time_now.strftime("%Y-%m-%d"),
        )

    @submissions_status.before_loop
    async def before_submissions_status(self):
        await self.bot.wait_until_ready()

    @submissions_status.error
    async def submissions_status_error(self, error):
        logger.error("Submissions status loop crashed; restarting.", exc_info=error)
        self.submissions_status.restart()
