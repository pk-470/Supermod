from discord.ext import commands, tasks
import pendulum

from features.submissions_status.subs_status_constants import *


class Submissions_Status(commands.Cog):
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
                f"Hello {LISTENERS_ROLE_MENTION}. "
                f"{self.bot.get_channel(SUBMISSIONS_CHANNEL).mention} is now open."
            )
            print(
                '"Submissions is open" message has been posted (date: '
                + time_now.strftime("%Y-%m-%d")
                + ")."
            )
        if (
            time_now.strftime("%A") == SUBMISSIONS_CLOSED_DAY
            and time_now.hour == SUBMISSIONS_CLOSED_HOUR
            and time_now.minute == SUBMISSIONS_CLOSED_MINUTE
        ):
            await self.bot.get_channel(ANNOUNCEMENTS_CHANNEL).send(
                f"Hello {LISTENERS_ROLE_MENTION}. "
                f"{self.bot.get_channel(SUBMISSIONS_CHANNEL).mention} is now closed and voting is open.\n"
                f"Go to the {self.bot.get_channel(VOTED_CHANNEL).mention} and use any of the :thumbs up: emoji "
                "on the album you would like to select, and our voting bot (Ultimate Polling) will send you "
                "a confirmation via DM. You may vote 10 times, max of 1 time per album.\n"
                "Good luck choosing!\n\n"
                "Use %help for a full list of commands for Ultimate Polling.\n\n"
                "*Note: If voting reactions are still not enabled an hour after this message, "
                f"then you should bring it up in* {self.bot.get_channel(TALK_TO_THE_STAFF_CHANNEL).mention}."
            )
            print(
                '"Submissions is closed" message has been posted (date: '
                + time_now.strftime("%Y-%m-%d")
                + ")."
            )
