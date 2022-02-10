# Library for Discord
from discord.ext import commands, tasks

# Google spreadsheets
import gspread

# Library to load tokens
from os import getenv

# Libraries for various functions
from random import choice
import pendulum

# Import data according to local_mode status
local_mode = open("mode_switch.txt", "r").read()

if local_mode == "ON":
    from dotenv import load_dotenv

    load_dotenv("tokens/.env")

    gsa = gspread.service_account("tokens/service_account.json")
else:
    from json import loads

    gsa = gspread.service_account_from_dict(loads(getenv("SERVICE_ACCOUNT_CRED")))


qotd_wks = gsa.open_by_url(getenv("QOTD_SHEET_URL")).sheet1


# Setting
qotd_channel = int(getenv("QOTD_CHANNEL"))
qotd_hour = 6


class QOTD(commands.Cog, description="Functions to set up and retrieve QOTD."):
    def __init__(self, bot):
        self.bot = bot
        self.qotd_loop.start()

    @commands.command(
        brief="Fetch a QOTD without marking it as used.",
        description="Fetch a QOTD without marking it as used.",
    )
    async def qotd(self, ctx):
        questions = qotd_wks.get_all_values()
        await ctx.send(qotd_get(questions)[2])

    # QOTD loop
    @tasks.loop(minutes=60)
    async def qotd_loop(self):
        print(
            "QOTD loop is working ("
            + pendulum.now().strftime("%Y-%m-%d, %H:%M:%S")
            + ")."
        )
        if pendulum.now().hour == qotd_hour:
            questions = qotd_wks.get_all_values()
            date_str = pendulum.now().strftime("%m/%#d/%Y")
            question = qotd_get(questions)
            await self.bot.get_channel(qotd_channel).send(
                "__**"
                + question[0]
                + " of the Day "
                + date_str
                + ":**__\n\n"
                + question[2]
            )
            question_row = qotd_wks.find(question[2]).row
            question_count = qotd_wks.cell(question_row, 3)
            if question_count:
                qotd_wks.update_cell(question_row, 4, 1)
            else:
                qotd_wks.update_cell(question_row, 4, int(question_count) + 1)
            print(
                "QOTD has been posted (date: "
                + pendulum.now().strftime("%Y-%m-%d")
                + ")."
            )


def qotd_get(questions):
    questions = [
        question
        for question in questions
        if question[2]
        and (question[1] == "N" and not question[3] or question[1] == "Y")
    ]
    question = choice(questions)
    return question


# Add cog to bot
def setup(bot):
    bot.add_cog(QOTD(bot))
