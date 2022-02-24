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
submissions_close_day = "Wednesday"
submissions_close_hour = 20


class Submissions_status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.submissions_status.start()

    # Submissions status announcement loop
    @tasks.loop(minutes=60)
    async def submissions_status(self):
        print(
            "Submissions status loop is working ("
            + pendulum.now("EST").strftime("%Y-%m-%d, %H:%M:%S EST")
            + ")."
        )
        if (
            pendulum.now("EST").strftime("%A") == submissions_open_day
            and pendulum.now("EST").hour == submissions_open_hour
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
                + pendulum.now("EST").strftime("%Y-%m-%d")
                + ")."
            )
        if (
            pendulum.now("EST").strftime("%A") == submissions_close_day
            and pendulum.now("EST").hour == submissions_close_hour
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
                + pendulum.now("EST").strftime("%Y-%m-%d")
                + ")."
            )


# Add cog to bot
def setup(bot):
    bot.add_cog(Submissions_status(bot))
