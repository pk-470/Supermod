import logging

import pendulum
from discord.ext import tasks
from discord.ext.commands import Bot, Cog

from supermod._mode_setup import is_local
from supermod._utils import text_channel
from supermod.features.submissions_status._constants import *

logger = logging.getLogger(__name__)


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
                announcements_channel = text_channel(self.bot, ANNOUNCEMENTS_CHANNEL)
                ol_weekly_playlist_channel = text_channel(
                    self.bot, OL_WEEKLY_PLAYLIST_CHANNEL
                )
                input_ratings_here_channel = text_channel(
                    self.bot, INPUT_RATINGS_HERE_CHANNEL
                )
                faqs_channel = text_channel(self.bot, FAQS_CHANNEL)
                talk_to_the_staff_channel = text_channel(
                    self.bot, TALK_TO_THE_STAFF_CHANNEL
                )
                if (
                    announcements_channel is None
                    or ol_weekly_playlist_channel is None
                    or input_ratings_here_channel is None
                    or faqs_channel is None
                    or talk_to_the_staff_channel is None
                ):
                    logger.warning(
                        "Submissions status loop: a required channel could not be "
                        "resolved for the 'open' announcement; skipping this tick."
                    )
                    return
                await announcements_channel.send(
                    f"Hello {LISTENERS_ROLE_MENTION}! "
                    + "Voting has closed and our new weekly picks are now available in the Albums Under Review category, "
                    + f"located below {ol_weekly_playlist_channel.mention}."
                    + f" When you have listened to an album in full, head to {input_ratings_here_channel.mention} "
                    + "and submit your score. "
                    + f"Check the {faqs_channel.mention} and the individual channel descriptions, "
                    + f"or head to {talk_to_the_staff_channel.mention} if you need further assistance."
                )
                logger.info(
                    "'Submissions is open' message has been posted (date: %s).",
                    time_now.strftime("%Y-%m-%d"),
                )
            if (
                time_now.strftime("%A") == SUBMISSIONS_CLOSED_DAY
                and time_now.hour == SUBMISSIONS_CLOSED_HOUR
                and time_now.minute == SUBMISSIONS_CLOSED_MINUTE
            ):
                announcements_channel = text_channel(self.bot, ANNOUNCEMENTS_CHANNEL)
                submissions_channel = text_channel(self.bot, SUBMISSIONS_CHANNEL)
                voted_channel = text_channel(self.bot, VOTED_CHANNEL)
                if (
                    announcements_channel is None
                    or submissions_channel is None
                    or voted_channel is None
                ):
                    logger.warning(
                        "Submissions status loop: a required channel could not be "
                        "resolved for the 'closed' announcement; skipping this tick."
                    )
                    return
                await announcements_channel.send(
                    f"Hello {LISTENERS_ROLE_MENTION}! "
                    + f"{submissions_channel.mention} is now closed and voting is open. "
                    + f"Head to {voted_channel.mention} where you can vote up to 5 albums "
                    + "using the :thumbsup: emoji. The winning album will be revealed along with the random picks "
                    + "during the upcoming weekend and will be reviewed next week."
                )
                logger.info(
                    "'Submissions is closed' message has been posted (date: %s).",
                    time_now.strftime("%Y-%m-%d"),
                )
        except Exception:
            logger.exception("Submissions status loop encountered an error.")
            return

    @submissions_status.before_loop
    async def before_submissions_status(self):
        await self.bot.wait_until_ready()

    @submissions_status.error
    async def submissions_status_error(self, error):
        logger.error("Submissions status loop crashed; restarting.", exc_info=error)
        self.submissions_status.restart()
