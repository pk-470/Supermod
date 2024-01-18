from discord.ext import commands, tasks
import pendulum

from features.promotions.promo_utils import *
from album_classes.album import remove_spaces
from mode_switch import LOCAL_MODE

# Exceptions
from discord import NotFound
from asyncio.exceptions import TimeoutError


class Promotions(
    commands.Cog, description="Set up promotions for #creators-friends-and-partners."
):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if LOCAL_MODE == "ON":
            print(
                f"{pendulum.now('America/Toronto').strftime('%Y-%m-%d %H:%M:%S EST')}: "
                + "Promotions loop will not start (LOCAL_MODE: ON)."
            )
        elif LOCAL_MODE == "OFF":
            self.promos_loop.start()

    @tasks.loop(minutes=60)
    async def promos_loop(self):
        time_now = pendulum.now("America/Toronto")
        promos_as_lists = PROMOS_WKS.get_all_values()[1:]
        for promo_as_list in promos_as_lists:
            promo_as_list = [remove_spaces(i) for i in promo_as_list]
            promo_as_list[5] = promo_as_list[5].split(":")[0]
            if promo_as_list[4].lower().startswith("last"):
                promo_as_list[4] = time_now._last_of_month().day
            if (time_now.day, time_now.hour) == (
                int(promo_as_list[4]),
                int(promo_as_list[5]),
            ):
                guild = self.bot.get_guild(SERVER)
                if promo_as_list[6] != "N/A":
                    try:
                        for member_id in promo_as_list[6].split(" "):
                            await guild.fetch_member(
                                int(remove_spaces(member_id)[3:-1])
                            )
                        post_in_channel = PROMOS_CHANNEL
                    except NotFound:
                        post_in_channel = REJECTED_PROMOS_CHANNEL
                        await self.bot.get_channel(REJECTED_PROMOS_CHANNEL).send(
                            "The following promo will not be posted because I can't "
                            "find at least one of its related members in the server:"
                        )
                    promo_formatted = promo_make(promo_as_list)
                    channel = self.bot.get_channel(post_in_channel)
                    await promo_post(promo_formatted, channel)
                else:
                    await self.bot.get_channel(PROMOS_CHANNEL).send(
                        f"**{promo_as_list[2]}**\n\n{promo_as_list[3]}"
                    )

    @commands.command(
        brief="Add a creator / partner for promotion.",
        description="Follow the bot's instructions to add a creator / partner for promotion.",
    )
    @commands.has_role(STAFF_ROLE)
    async def promo_add(self, ctx: commands.Context):
        try:
            await promo_add_interaction(self.bot, ctx)
        except TimeoutError:
            await ctx.send("Time has run out.")
        except:
            await ctx.send("Something went wrong. Please try again.")
