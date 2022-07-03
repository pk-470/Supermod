# Library for Discord
from discord.ext import commands, tasks

# Library to load tokens
from os import getenv

# Libraries for various functions
import pendulum

# Import data according to local_mode status
local_mode = open("mode_switch.txt", "r").read()

if local_mode == "ON":
    from dotenv import load_dotenv

    load_dotenv("tokens/.env")


# Setting
ANNOUNCEMENTS_CHANNEL = int(getenv("ANNOUNCEMENTS_CHANNEL"))
SUBMISSIONS_CHANNEL = int(getenv("SUBMISSIONS_CHANNEL"))
VOTED_CHANNEL = int(getenv("VOTED_CHANNEL"))
TALK_TO_THE_STAFF_CHANNEL = int(getenv("TALK_TO_THE_STAFF_CHANNEL"))

LISTENERS_ROLE_MENTION = "<@&" + str(getenv("LISTENERS_ROLE")) + ">"

SUBMISSIONS_OPEN_DAY = "Sunday"
SUBMISSIONS_OPEN_HOUR = 0
SUBMISSIONS_OPEN_MINUTE = 0
SUBMISSIONS_CLOSED_DAY = "Thursday"
SUBMISSIONS_CLOSED_HOUR = 0
SUBMISSIONS_CLOSED_MINUTE = 0


class Submissions_status(commands.Cog):
    def __init__(self, bot):
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


# Add cog to bot
def setup(bot):
    bot.add_cog(Submissions_status(bot))
