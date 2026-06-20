import pendulum
from discord.ext import tasks
from discord.ext.commands import Bot, Cog

from supermod._mode_setup import is_local
from supermod._utils import print_info
from supermod.features.submissions_status._constants import *


class SubmissionsStatus(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        if is_local():
            print_info("Submissions status loop will not start (local mode).")
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
                announcements_channel = self.bot.get_channel(ANNOUNCEMENTS_CHANNEL)
                ol_weekly_playlist_channel = self.bot.get_channel(
                    OL_WEEKLY_PLAYLIST_CHANNEL
                )
                input_ratings_here_channel = self.bot.get_channel(
                    INPUT_RATINGS_HERE_CHANNEL
                )
                faqs_channel = self.bot.get_channel(FAQS_CHANNEL)
                talk_to_the_staff_channel = self.bot.get_channel(
                    TALK_TO_THE_STAFF_CHANNEL
                )
                if (
                    announcements_channel is None
                    or ol_weekly_playlist_channel is None
                    or input_ratings_here_channel is None
                    or faqs_channel is None
                    or talk_to_the_staff_channel is None
                ):
                    print_info(
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
                print_info(
                    "'Submissions is open' message has been posted (date: "
                    + time_now.strftime("%Y-%m-%d")
                    + ")."
                )
            if (
                time_now.strftime("%A") == SUBMISSIONS_CLOSED_DAY
                and time_now.hour == SUBMISSIONS_CLOSED_HOUR
                and time_now.minute == SUBMISSIONS_CLOSED_MINUTE
            ):
                announcements_channel = self.bot.get_channel(ANNOUNCEMENTS_CHANNEL)
                submissions_channel = self.bot.get_channel(SUBMISSIONS_CHANNEL)
                voted_channel = self.bot.get_channel(VOTED_CHANNEL)
                if (
                    announcements_channel is None
                    or submissions_channel is None
                    or voted_channel is None
                ):
                    print_info(
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
                print_info(
                    "'Submissions is closed' message has been posted (date: "
                    + time_now.strftime("%Y-%m-%d")
                    + ")."
                )
        except Exception as e:
            print_info(f"Submissions status loop encountered an error: {e}")
            return

    @submissions_status.before_loop
    async def before_submissions_status(self):
        await self.bot.wait_until_ready()

    @submissions_status.error
    async def submissions_status_error(self, error):
        print_info(f"Submissions status loop crashed; restarting. Error: {error}")
        self.submissions_status.restart()
