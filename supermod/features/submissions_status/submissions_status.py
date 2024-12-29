import pendulum
from discord.ext import commands, tasks

from .subs_status_constants import *


class SubmissionsStatus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.submissions_status.start()

    # Submissions status announcement loop
    @tasks.loop(minutes=1)
    async def submissions_status(self):
        time_now = pendulum.now("America/Toronto")
        if (
            time_now.strftime("%A") == SUBMISSIONS_OPEN_DAY
            and time_now.hour == SUBMISSIONS_OPEN_HOUR
            and time_now.minute == SUBMISSIONS_OPEN_MINUTE
        ):
            await self.bot.get_channel(ANNOUNCEMENTS_CHANNEL).send(
                f"Hello {LISTENERS_ROLE_MENTION}! "
                + "Voting has closed and our new weekly picks are now available in the Albums Under Review category, "
                + f"located below {self.bot.get_channel(OL_WEEKLY_PLAYLIST_CHANNEL).mention}."
                + f"When you have listened to an album in full, head to {self.bot.get_channel(INPUT_RATINGS_HERE_CHANNEL).mention} "
                + "and submit your score. "
                + f"Check the {self.bot.get_channel(FAQS_CHANNEL).mention} and the individual channel descriptions, "
                + f"or head to {self.bot.get_channel(TALK_TO_THE_STAFF_CHANNEL).mention} if you need further assistance."
            )
            print(
                "'Submissions is open' message has been posted (date: "
                + time_now.strftime("%Y-%m-%d")
                + ")."
            )
        if (
            time_now.strftime("%A") == SUBMISSIONS_CLOSED_DAY
            and time_now.hour == SUBMISSIONS_CLOSED_HOUR
            and time_now.minute == SUBMISSIONS_CLOSED_MINUTE
        ):
            await self.bot.get_channel(ANNOUNCEMENTS_CHANNEL).send(
                f"Hello {LISTENERS_ROLE_MENTION}! "
                + f"{self.bot.get_channel(SUBMISSIONS_CHANNEL).mention} is now closed and voting is open. "
                + f"Head to {self.bot.get_channel(VOTED_CHANNEL).mention} where you can vote up to 10 albums "
                + "using the :thumbs up: emoji. The winning album will be revealed along with the random picks "
                + "during the upcoming weekend and will be reviewed next week."
            )
            print(
                "'Submissions is closed' message has been posted (date: "
                + time_now.strftime("%Y-%m-%d")
                + ")."
            )
