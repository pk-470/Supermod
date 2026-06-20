from asyncio.exceptions import TimeoutError  # pylint: disable=redefined-builtin
from typing import Optional

import pendulum
from discord import Message, Reaction, User
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Cog, Context

from supermod._mode_setup import is_local
from supermod._utils import *
from supermod.features.qotd._constants import *
from supermod.features.qotd._utils import *


class QOTD(Cog, description="Submit and retrieve a QOTD."):
    def __init__(self, bot: Bot):
        self.bot = bot

        if is_local():
            print_info("QOTD loop will not start (local mode).")
        else:
            self.qotd_loop.start()

    @tasks.loop(minutes=1)
    async def qotd_loop(self):
        try:
            time_now = pendulum.now("America/Toronto")
            if time_now.hour == QOTD_HOUR and time_now.minute == QOTD_MINUTE:
                channel = self.bot.get_channel(QOTD_APPROVAL_CHANNEL)
                if channel is None:
                    print_info(
                        f"QOTD approval channel ({QOTD_APPROVAL_CHANNEL}) not found. "
                        + "Skipping this QOTD loop tick."
                    )
                    return
                await self._qotd_interact(
                    channel, timeout=1800  # type: ignore[reportArgumentType]
                )
        except Exception as e:
            print_info(
                f"Error in qotd_loop tick ({type(e).__name__}: {e}). "
                + "Skipping this QOTD loop tick."
            )
            return

    @qotd_loop.before_loop
    async def before_qotd_loop(self) -> None:
        await self.bot.wait_until_ready()

    @qotd_loop.error
    async def qotd_loop_error(self, error: Exception) -> None:
        print_info(
            f"qotd_loop crashed ({type(error).__name__}: {error}). Restarting loop."
        )
        self.qotd_loop.restart()

    @commands.command(
        brief="Fetch a QOTD.",
        description="Fetch a QOTD. React with a green checkmark to post the question and "
        + "mark it as used, with a red X to reject the question, and with E to post an "
        + "edited version of the question and mark the original as used.",
    )
    @commands.has_role(STAFF_ROLE)
    async def qotd(self, ctx: Context):
        await self._qotd_interact(ctx, timeout=60)

    @commands.command(
        brief="Add a question / activity to the spreadsheet.",
        description="Follow the bot's instructions to add a question / activity to the spreadsheet.",
    )
    @commands.has_role(STAFF_ROLE)
    async def qotd_add(self, ctx: Context):
        def check(resp: Message):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            await ctx.send("Respond with 'stop' at any point to stop the process.")
            await ctx.send("QOTD type (Question / Activity):")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The QOTD submission process has stopped.")
                return
            if response.content.lower().startswith("q"):
                qotd_type = "Question"
            elif response.content.lower().startswith("a"):
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
            if response.content.lower().startswith("y"):
                repeatable = "Y"
                repeatable_long = "repeatable"
            elif response.content.lower().startswith("n"):
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
            if response.content.lower().startswith("y"):
                QOTD_WKS.append_row([qotd_type, repeatable, qotd])
                await ctx.send("The QOTD was added to the spreadsheet.")
            elif response.content.lower().startswith("n"):
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
            print_info(f"{type(e).__name__}: {e}")
            await ctx.send("Something went wrong. Please try again.")

    @commands.command(
        brief="Reset the number of uses for all questions to 0.",
        description="Reset the number of uses for all questions to 0.",
    )
    @commands.has_role(STAFF_ROLE)
    async def qotd_reset(self, ctx: Context):
        q_rows = QOTD_WKS.get_all_values()
        for i, q_row in enumerate(q_rows[1:], start=2):
            if q_row[2]:
                QOTD_WKS.update_cell(i, 4, 0)

        await ctx.send("Number of uses for all questions set to 0.")

    async def _qotd_interact(self, ctx: Context, timeout):
        question = qotd_get()
        if question is None:
            await ctx.send("There are no questions available.")
            return
        qotd = await ctx.send(question[2])
        await qotd.add_reaction("✅")
        await qotd.add_reaction("❌")
        await qotd.add_reaction("🇪")

        def check_reaction_1(reaction: Reaction, user: User):
            return (
                str(reaction.emoji) in ("✅", "❌", "🇪")
                and user != self.bot.user
                and reaction.message.id == qotd.id
            )

        try:
            reaction: Reaction
            user: User
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=timeout, check=check_reaction_1
            )
            if str(reaction.emoji) == "✅":
                await self._qotd_post(question, self.bot, ctx)
            elif str(reaction.emoji) == "❌":
                await ctx.send("The QOTD was rejected.")
            elif str(reaction.emoji) == "🇪":
                await ctx.send(
                    f"Respond with an edited version of the {question[0].lower()} "
                    + f"which I will post instead (I will mark the original {question[0].lower()} "
                    + "as used in the spreadsheet without changing its template). "
                    + "Respond with 'stop' if you want me to stop waiting for a response."
                )

                def check_author(response: Message):
                    return response.author == user

                response = await self.bot.wait_for(
                    "message", timeout=600, check=check_author
                )
                if response.content.lower() == "stop":
                    await ctx.send("The QOTD editing process has stopped.")
                    return
                await ctx.send("The following will be posted as QOTD:")
                qotd = await ctx.send(response.content)
                await qotd.add_reaction("✅")
                await qotd.add_reaction("❌")

                def check_reaction_2(reaction: Reaction, user: User):
                    return (
                        str(reaction.emoji) in ("✅", "❌")
                        and user != self.bot.user
                        and reaction.message.id == qotd.id
                    )

                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60, check=check_reaction_2
                )
                if str(reaction.emoji) == "✅":
                    await self._qotd_post(
                        question, self.bot, ctx, overwrite=response.content
                    )
                elif str(reaction.emoji) == "❌":
                    await ctx.send("The QOTD was rejected.")

        except TimeoutError:
            await ctx.send("Time has run out.")

    async def _qotd_post(
        self,
        question: list[str],
        bot: Bot,
        ctx: Context,
        overwrite: Optional[str] = None,
    ):
        time_now = pendulum.now("America/Toronto")
        date_str = time_now.strftime("%m/%-d/%Y")
        channel = bot.get_channel(QOTD_CHANNEL)
        if channel is None:
            print_info(
                f"QOTD channel ({QOTD_CHANNEL}) not found. The QOTD was not posted."
            )
            return
        if overwrite is None:
            await channel.send(
                f"__**{question[0].capitalize()} of the Day {date_str}:**__"
                + f"\n\n{question[2]}"
            )
        else:
            await channel.send(
                f"__**{question[0].capitalize()} of the Day {date_str}:**__"
                + f"\n\n{overwrite}"
            )
        mark_as_used(question)
        conf_msg = f"QOTD has been posted ({date_str})."
        print_info(conf_msg)
        await ctx.send(conf_msg)
