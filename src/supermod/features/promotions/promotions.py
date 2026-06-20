import re
from asyncio.exceptions import TimeoutError  # pylint: disable=redefined-builtin

import pendulum
from discord import Message, NotFound, TextChannel
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Cog, Context

from supermod._mode_setup import is_local
from supermod._utils import *
from supermod.features.newsletter._utils import ordinal
from supermod.features.promotions._utils import *


class Promotions(
    Cog, description="Set up promotions for #creators-friends-and-partners."
):
    def __init__(self, bot: Bot):
        self.bot = bot

        if is_local():
            print_info("Promotions loop will not start (local mode).")
        else:
            self.promos_loop.start()

    @tasks.loop(minutes=60)
    async def promos_loop(self):
        time_now = pendulum.now("America/Toronto")
        promos_as_lists = PROMOS_WKS.get_all_values()[1:]
        for promo_as_list in promos_as_lists:
            try:
                promo_as_list = [i.strip() for i in promo_as_list]
                promo_as_list[5] = promo_as_list[5].split(":")[0]
                if promo_as_list[4].lower().startswith("last"):
                    promo_as_list[4] = time_now.last_of("month").day
                if (time_now.day, time_now.hour) == (
                    int(promo_as_list[4]),
                    int(promo_as_list[5]),
                ):
                    guild = self.bot.get_guild(SERVER)
                    if guild is None:
                        print_info(
                            f"Could not find guild with ID {SERVER}; skipping this tick."
                        )
                        return
                    if promo_as_list[6] != "N/A":
                        try:
                            for member_id in promo_as_list[6].split(" "):
                                match = re.search(r"\d+", member_id)
                                if match is None:
                                    print_info(
                                        f"Could not parse member id from '{member_id}'; skipping it."
                                    )
                                    continue
                                await guild.fetch_member(int(match.group()))
                            post_in_channel = PROMOS_CHANNEL
                        except NotFound:
                            post_in_channel = REJECTED_PROMOS_CHANNEL
                            rejected_channel = self.bot.get_channel(
                                REJECTED_PROMOS_CHANNEL
                            )
                            if rejected_channel is None:
                                print_info(
                                    f"Could not find rejected promos channel with ID "
                                    f"{REJECTED_PROMOS_CHANNEL}; skipping this promo."
                                )
                                continue
                            await rejected_channel.send(
                                "The following promo will not be posted because I can't "
                                + "find at least one of its related members in the server:"
                            )
                        promo_formatted = promo_make(promo_as_list)
                        channel = self.bot.get_channel(post_in_channel)
                        if channel is None:
                            print_info(
                                f"Could not find channel with ID {post_in_channel}; "
                                "skipping this promo."
                            )
                            continue
                        await self._promo_post(promo_formatted, channel)  # type: ignore[reportArgumentType]
                    else:
                        channel = self.bot.get_channel(PROMOS_CHANNEL)
                        if channel is None:
                            print_info(
                                f"Could not find promos channel with ID {PROMOS_CHANNEL}; "
                                "skipping this promo."
                            )
                            continue
                        await channel.send(
                            f"**{promo_as_list[2]}**\n\n{promo_as_list[3]}"
                        )
            except Exception as e:
                print_info(
                    f"Error processing promo row {promo_as_list}: {type(e).__name__}: {e}"
                )
                continue

    @promos_loop.before_loop
    async def before_promos_loop(self) -> None:
        await self.bot.wait_until_ready()

    @promos_loop.error
    async def promos_loop_error(self, error: Exception) -> None:
        print_info(
            f"Promos loop raised {type(error).__name__}: {error}; restarting loop."
        )
        self.promos_loop.restart()

    @commands.command(
        brief="Add a creator / partner for promotion.",
        description="Follow the bot's instructions to add a creator / partner for promotion.",
    )
    @commands.has_role(STAFF_ROLE)
    async def promo_add(self, ctx: Context):
        try:
            await self._promo_add_interaction(ctx)
        except TimeoutError:
            await ctx.send("Time has run out.")
        except Exception as e:
            print_info(f"{type(e).__name__}: {e}")
            await ctx.send("Something went wrong. Please try again.")

    async def _promo_post(
        self, promo_formatted: Embed | str, channel: TextChannel | Context
    ) -> None:
        """Post a promo in a channel."""
        # Embed
        if isinstance(promo_formatted, Embed):
            await channel.send(embed=promo_formatted)
        # No embed
        elif isinstance(promo_formatted, str):
            await channel.send(promo_formatted)

    async def _promo_add_interaction(self, ctx: Context) -> None:
        dates = [f"{promo[4]}/{promo[5]}" for promo in PROMOS_WKS.get_all_values()[1:]]
        new_promo_data = []

        def check(resp: Message):
            return resp.author == ctx.author and resp.channel == ctx.channel

        # Starting message
        await ctx.send("Respond with 'stop' at any point to stop the process.")

        # Submitter type (creator / partner)
        await ctx.send("Submitter Type (Creator / Partner):")
        response = await self.bot.wait_for("message", timeout=30, check=check)
        if response.content.lower() == "stop":
            await ctx.send("The promo submission process has stopped.")
            return
        if response.content.lower().startswith("c"):
            embed = "Yes"
        elif response.content.lower().startswith("p"):
            embed = "No"
        else:
            await ctx.send(
                f"I don't know what you mean by '{response.content}'. "
                + "Please start the promo submission process again."
            )
            return
        new_promo_data.extend([response.content.capitalize(), embed])

        # Project name
        await ctx.send("Project Name:")
        response = await self.bot.wait_for("message", timeout=30, check=check)
        if response.content.lower() == "stop":
            await ctx.send("The promo submission process has stopped.")
            return
        new_promo_data.append(response.content.capitalize())

        # Promo content
        await ctx.send("Message (no mentions on top):")
        response = await self.bot.wait_for("message", timeout=90, check=check)
        if response.content.lower() == "stop":
            await ctx.send("The promo submission process has stopped.")
            return
        new_promo_data.append(response.content)

        # Choose date/time
        await ctx.send(
            "Date/Time (e.g. 11/4:00). Dates/Times which are already taken: "
            + ", ".join(dates)
        )
        response = await self.bot.wait_for("message", timeout=90, check=check)
        if response.content.lower() == "stop":
            await ctx.send("The promo submission process has stopped.")
            return
        new_date = response.content.split("/")
        new_promo_data.extend(new_date)

        # Member ID(s)
        await ctx.send(
            "Member ID(s) (in the format 'number_1 number_2' etc. without any commas or <@!, >):"
        )
        response = await self.bot.wait_for("message", timeout=90, check=check)
        if response.content.lower() == "stop":
            await ctx.send("The promo submission process has stopped.")
            return
        new_promo_data.append(
            " ".join([f"<@!{id}>" for id in response.content.split(" ") if id])
        )

        # Make and show promo
        new_promo_formatted = promo_make(new_promo_data)
        await ctx.send(
            f"The new promo will appear every {new_date[0]} {ordinal(int(new_date[0]))} "
            + f"day of each month at {new_date[1]} as follows:"
        )
        await self._promo_post(new_promo_formatted, ctx)

        # Ask for approval
        await ctx.send("Do you want to submit (y/n)?")
        confirm = await self.bot.wait_for("message", timeout=30, check=check)
        if confirm.content.lower().startswith("y"):
            PROMOS_WKS.append_row(new_promo_data)
            await ctx.send("The promo was submitted.")
        elif confirm.content.lower().startswith("n"):
            await ctx.send("The promo was rejected.")
        else:
            await ctx.send(
                f"I don't know what you mean by '{confirm.content}'. "
                + "Please start the promo submission process again."
            )
            return
