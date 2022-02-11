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


# Setting
qotd_wks = gsa.open_by_url(getenv("QOTD_SHEET_URL")).sheet1

qotd_channel = int(getenv("QOTD_CHANNEL"))
activities_channel = int(getenv("ACTIVITIES_CHANNEL"))

qotd_hour = 18


class QOTD(commands.Cog, description="Retrieve a QOTD."):
    def __init__(self, bot):
        self.bot = bot
        self.qotd_loop.start()

    @commands.command(
        brief="Fetch a QOTD. Add the option `mark' to mark the question as used.",
        description="Fetch a QOTD. Add the option `mark' to mark the question as used.",
    )
    async def qotd(self, ctx, mark=None):
        questions = qotd_wks.get_all_values()
        question = qotd_get(questions)
        await ctx.send(question[2])
        if mark == "mark":
            mark_as_used(question)

    # QOTD loop
    @tasks.loop(minutes=60)
    async def qotd_loop(self):
        print(
            "QOTD loop is working ("
            + pendulum.now("EST").strftime("%Y-%m-%d, %H:%M:%S EST")
            + ")."
        )
        if pendulum.now("EST").hour == qotd_hour:
            questions = qotd_wks.get_all_values()
            date_str = pendulum.now("EST").strftime("%m/%#d/%Y")
            question = qotd_get(questions)
            if question[0].lower() == "question":
                await self.bot.get_channel(qotd_channel).send(
                    "__**Question of the Day " + date_str + ":**__\n\n" + question[2]
                )
                print(
                    "QOTD has been posted (date: "
                    + pendulum.now("EST").strftime("%Y-%m-%d")
                    + ")."
                )
            else:
                await self.bot.get_channel(activities_channel).send(
                    "Activity of the Day "
                    + date_str
                    + "(adapt as required):\n\n"
                    + question[2]
                )
                print(
                    "Activity of the Day has been submitted for posting (date: "
                    + pendulum.now("EST").strftime("%Y-%m-%d")
                    + ")."
                )

            mark_as_used(question)


def qotd_get(questions):
    questions = [
        question
        for question in questions
        if question[2]
        and (question[1] == "N" and not question[3] or question[1] == "Y")
    ]
    question = choice(questions)
    return question


def mark_as_used(question):
    question_row = qotd_wks.find(question[2]).row
    question_count = qotd_wks.cell(question_row, 3)
    if question_count:
        qotd_wks.update_cell(question_row, 4, 1)
    else:
        qotd_wks.update_cell(question_row, 4, int(question_count) + 1)


# Add cog to bot
def setup(bot):
    bot.add_cog(QOTD(bot))
