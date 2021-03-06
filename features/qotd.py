# Library for Discord
from discord.ext import commands, tasks

# Google spreadsheets
import gspread

# Library to load tokens
from os import getenv

# Libraries for various functions
from random import choice
from asyncio.exceptions import TimeoutError
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
QOTD_WKS = gsa.open_by_url(getenv("QOTD_SHEET_URL")).sheet1

QOTD_CHANNEL = int(getenv("QOTD_CHANNEL"))
QOTD_APPROVAL_CHANNEL = int(getenv("QOTD_APPROVAL_CHANNEL"))

QOTD_HOUR = 6
QOTD_MINUTE = 0


class QOTD(commands.Cog, description="Submit and retrieve a QOTD."):
    def __init__(self, bot):
        self.bot = bot
        self.qotd_loop.start()

    @commands.command(
        brief="Fetch a QOTD.",
        description="Fetch a QOTD. React with a green checkmark to post the question and "
        "mark it as used, with a red X to reject the question, and with E to post an "
        "edited version of the question and mark the original as used.",
    )
    async def qotd(self, ctx):
        await qotd_interact(self.bot, ctx, timeout=60)

    @commands.command(
        brief="Add a question / activity to the spreadsheet.",
        description="Follow the bot's instructions to add a question / activity to the spreadsheet.",
    )
    async def qotd_add(self, ctx):
        def check(resp):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            await ctx.send("Respond with 'stop' at any point to stop the process.")
            await ctx.send("QOTD type (Question / Activity):")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The QOTD submission process has stopped.")
                return
            elif response.content.lower()[0] == "q":
                qotd_type = "Question"
            elif response.content.lower()[0] == "a":
                qotd_type = "Activity"
            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    "Please start the QOTD submission process again."
                )
                return
            await ctx.send("Repeatable (Yes / No):")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The QOTD submission process has stopped.")
                return
            elif response.content.lower()[0] == "y":
                repeatable = "Y"
                repeatable_long = "repeatable"
            elif response.content.lower()[0] == "n":
                repeatable = "N"
                repeatable_long = "non-repeatable"
            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    "Please start the QOTD submission process again."
                )
                return
            await ctx.send("QOTD content:")
            response = await self.bot.wait_for("message", timeout=180, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The QOTD submission process has stopped.")
                return
            else:
                qotd = response.content
            await ctx.send(
                f"The {qotd_type.lower()} '{qotd}' ({repeatable_long}) "
                "will be added to the spreadsheet. Do you want to submit (y/n)?"
            )
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower()[0] == "y":
                QOTD_WKS.append_row([qotd_type, repeatable, qotd])
                await ctx.send("The QOTD was added to the spreadsheet.")
            elif response.content.lower()[0] == "n":
                await ctx.send("The QOTD was not added to the spreadsheet.")
            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    "Please start the QOTD submission process again."
                )
                return

        except TimeoutError:
            await ctx.send("Time has run out.")
        except:
            await ctx.send("Something went wrong. Please try again.")

    # QOTD loop
    @tasks.loop(minutes=1)
    async def qotd_loop(self):
        time_now = pendulum.now("America/Toronto")
        if time_now.hour == QOTD_HOUR and time_now.minute == QOTD_MINUTE:
            await qotd_interact(
                self.bot, self.bot.get_channel(QOTD_APPROVAL_CHANNEL), timeout=1800
            )


async def qotd_interact(bot, channel, timeout):
    question = qotd_get()
    qotd = await channel.send(question[2])
    await qotd.add_reaction(emoji="???")
    await qotd.add_reaction(emoji="???")
    await qotd.add_reaction(emoji="????")

    def check(reaction, user):
        return str(reaction.emoji) in ("???", "???", "????") and user != bot.user

    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=timeout, check=check
        )
        if str(reaction.emoji) == "???":
            await qotd_post(question, bot, channel)
        elif str(reaction.emoji) == "???":
            await channel.send("The QOTD was rejected.")
        elif str(reaction.emoji) == "????":
            await channel.send(
                f"Respond with an edited version of the {question[0].lower()} "
                f"which I will post instead (I will mark the original {question[0].lower()} "
                "as used in the spreadsheet without changing its template). "
                "Respond with 'stop' if you want me to stop waiting for a response."
            )

            def check(response):
                return response.author == user

            response = await bot.wait_for("message", timeout=600, check=check)
            if response.content.lower() == "stop":
                await channel.send("The QOTD editing process has stopped.")
                return
            await channel.send("The following will be posted as QOTD:")
            qotd = await channel.send(response.content)
            await qotd.add_reaction(emoji="???")
            await qotd.add_reaction(emoji="???")

            def check(reaction, user):
                return str(reaction.emoji) in ("???", "???") and user != bot.user

            reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
            if str(reaction.emoji) == "???":
                await qotd_post(question, bot, channel, overwrite=response.content)
            elif str(reaction.emoji) == "???":
                await channel.send("The QOTD was rejected.")

    except TimeoutError:
        await channel.send("Time has run out.")


def qotd_get():
    questions = QOTD_WKS.get_all_values()
    questions = [
        question
        for question in questions
        if question[2]
        and (question[1] == "N" and not question[3] or question[1] == "Y")
    ]
    question_full = choice(questions)
    return question_full


def mark_as_used(question):
    question_row = QOTD_WKS.find(question[2]).row
    question_count = QOTD_WKS.cell(question_row, 3)
    if question_count:
        QOTD_WKS.update_cell(question_row, 4, 1)
    else:
        QOTD_WKS.update_cell(question_row, 4, int(question_count) + 1)


async def qotd_post(question, bot, ctx, overwrite=None):
    time_now = pendulum.now("America/Toronto")
    date_str = time_now.strftime("%m/%#d/%Y")
    if overwrite is None:
        await bot.get_channel(QOTD_CHANNEL).send(
            f"__**{question[0].capitalize()} of the Day {date_str}:**__"
            f"\n\n{question[2]}"
        )
    else:
        await bot.get_channel(QOTD_CHANNEL).send(
            f"__**{question[0].capitalize()} of the Day {date_str}:**__"
            f"\n\n{overwrite}"
        )
    mark_as_used(question)
    conf_msg = f"QOTD has been posted ({date_str})."
    await ctx.send(conf_msg)
    print(conf_msg)


# Add cog to bot
def setup(bot):
    bot.add_cog(QOTD(bot))
