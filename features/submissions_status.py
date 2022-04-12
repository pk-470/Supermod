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
announcements_channel = int(getenv("ANNOUNCEMENTS_CHANNEL"))
submissions_channel = int(getenv("SUBMISSIONS_CHANNEL"))
voted_channel = int(getenv("VOTED_CHANNEL"))

listeners_role_mention = "<@&" + str(getenv("LISTENERS_ROLE")) + ">"

submissions_open_day = "Saturday"
submissions_open_hour = 20
submissions_open_minute = 0
submissions_closed_day = "Wednesday"
submissions_closed_hour = 20
submission_closed_minute = 0


class Submissions_status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.submissions_status.start()

    # Submissions status announcement loop
    @tasks.loop(minutes=1)
    async def submissions_status(self):
        time_now = pendulum.now("America/Toronto")
        print(
            "Submissions status loop is working ("
            + time_now.strftime("%Y-%m-%d, %H:%M:%S EST")
            + ")."
        )
        if (
            time_now.strftime("%A") == submissions_open_day
            and time_now.hour == submissions_open_hour
            and time_now.minute == submissions_open_minute
        ):
            await self.bot.get_channel(announcements_channel).send(
                "Hello "
                + listeners_role_mention
                + ". "
                + self.bot.get_channel(submissions_channel).mention
                + " is now open."
            )
            print(
                '"Submissions is open" message has been posted (date: '
                + time_now.strftime("%Y-%m-%d")
                + ")."
            )
        if (
            time_now.strftime("%A") == submissions_closed_day
            and time_now.hour == submissions_closed_hour
            and time_now.minute == submission_closed_minute
        ):
            await self.bot.get_channel(announcements_channel).send(
                "Hello "
                + listeners_role_mention
                + ". "
                + self.bot.get_channel(submissions_channel).mention
                + " is now closed and voting is open.\nGo to the "
                + self.bot.get_channel(voted_channel).mention
                + " and use any of the :thumbs up: emoji on the album you would like"
                + " to select and our voting bot will send you a confirmation via DM."
                + " You may vote 10 times, max of 1 time per album.\n Good luck choosing!"
                + "\n\nUse %help for a full list of commands."
            )
            print(
                '"Submissions is closed" message has been posted (date: '
                + time_now.strftime("%Y-%m-%d")
                + ")."
            )


# Add cog to bot
def setup(bot):
    bot.add_cog(Submissions_status(bot))
