from asyncio.exceptions import TimeoutError

import pendulum
from discord import Message
from discord.ext import commands, tasks

from ...mode_switch import LOCAL_MODE
from ...utils import *
from .qotd_constants import *
from .qotd_utils import *


class QOTD(commands.Cog, description="Submit and retrieve a QOTD."):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if LOCAL_MODE == "ON":
            print_info("QOTD loop will not start (LOCAL_MODE: ON).")
        else:
            self.qotd_loop.start()

    @tasks.loop(minutes=1)
    async def qotd_loop(self):
        time_now = pendulum.now("America/Toronto")
        if time_now.hour == QOTD_HOUR and time_now.minute == QOTD_MINUTE:
            await qotd_interact(
                self.bot, self.bot.get_channel(QOTD_APPROVAL_CHANNEL), timeout=1800
            )

    @commands.command(
        brief="Fetch a QOTD.",
        description="Fetch a QOTD. React with a green checkmark to post the question and "
        + "mark it as used, with a red X to reject the question, and with E to post an "
        + "edited version of the question and mark the original as used.",
    )
    @commands.has_role(STAFF_ROLE)
    async def qotd(self, ctx: commands.Context):
        await qotd_interact(self.bot, ctx, timeout=60)

    @commands.command(
        brief="Add a question / activity to the spreadsheet.",
        description="Follow the bot's instructions to add a question / activity to the spreadsheet.",
    )
    @commands.has_role(STAFF_ROLE)
    async def qotd_add(self, ctx: commands.Context):
        def check(resp: Message):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            await ctx.send("Respond with 'stop' at any point to stop the process.")
            await ctx.send("QOTD type (Question / Activity):")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The QOTD submission process has stopped.")
                return
            if response.content.lower()[0] == "q":
                qotd_type = "Question"
            elif response.content.lower()[0] == "a":
                qotd_type = "Activity"
            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    + "Please start the QOTD submission process again."
                )
                return
            await ctx.send("Repeatable (Yes / No):")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The QOTD submission process has stopped.")
                return
            if response.content.lower()[0] == "y":
                repeatable = "Y"
                repeatable_long = "repeatable"
            elif response.content.lower()[0] == "n":
                repeatable = "N"
                repeatable_long = "non-repeatable"
            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    + "Please start the QOTD submission process again."
                )
                return
            await ctx.send("QOTD content:")
            response = await self.bot.wait_for("message", timeout=180, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The QOTD submission process has stopped.")
                return
            qotd = response.content
            await ctx.send(
                f"The {qotd_type.lower()} '{qotd}' ({repeatable_long}) "
                + "will be added to the spreadsheet. Do you want to submit (y/n)?"
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
                    + "Please start the QOTD submission process again."
                )
                return

        except TimeoutError:
            await ctx.send("Time has run out.")
        except Exception as e:
            print_info(e)
            await ctx.send("Something went wrong. Please try again.")

    @commands.command(
        brief="Reset the number of uses for all questions to 0.",
        description="Reset the number of uses for all questions to 0.",
    )
    @commands.has_role(STAFF_ROLE)
    async def qotd_reset(self, ctx: commands.Context):
        q_rows = QOTD_WKS.get_all_values()
        for i, q_row in enumerate(q_rows):
            if q_row[2]:
                QOTD_WKS.update_cell(i + 1, 4, 0)

        await ctx.send("Number of uses for all questions set to 0.")
