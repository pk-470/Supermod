# Libraries for Discord
from discord import Embed, Color
from discord.ext import commands, tasks

# Google spreadsheets
import gspread

# Library to load tokens
from os import getenv

# Import remove_spaces
from classes.album_class import remove_spaces

# Import post_split
from features.releases import ordinal, post_split

# Libraries for various functions
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
PROMOS_WKS = gsa.open_by_url(getenv("QOTD_SHEET_URL")).get_worksheet(1)

SERVER = int(getenv("SERVER"))
PROMOS_CHANNEL = int(getenv("PROMOS_CHANNEL"))
REJECTED_PROMOS_CHANNEL = int(getenv("QOTD_APPROVAL_CHANNEL"))


class Promotions(
    commands.Cog, description="Set up promotions for #creators-friends-and-partners."
):
    def __init__(self, bot):
        self.bot = bot
        self.ads_loop.start()

    @commands.command(
        brief="Add a creator / partner for promotion.",
        description="Follow the bot's instructions to add a creator / partner for promotion.",
    )
    async def promo_add(self, ctx):
        dates = [f"{promo[4]}/{promo[5]}" for promo in PROMOS_WKS.get_all_values()[1:]]
        new_promo = []

        def check(resp):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            await ctx.send("Respond with 'stop' at any point to stop the process.")
            await ctx.send("Submitter Type (Creator / Partner):")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The promo submission process has stopped.")
                return
            elif response.content.lower()[0] == "c":
                embed = "Yes"
            elif response.content.lower()[0] == "p":
                embed = "No"
            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    "Please start the promo submission process again."
                )
                return
            new_promo.extend([response.content.capitalize(), embed])
            await ctx.send("Project Name:")
            response = await self.bot.wait_for("message", timeout=30, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The promo submission process has stopped.")
                return
            new_promo.append(response.content.capitalize())
            await ctx.send("Message (no mentions on top):")
            response = await self.bot.wait_for("message", timeout=90, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The promo submission process has stopped.")
                return
            new_promo.append(response.content)
            await ctx.send(
                "Date/Time (e.g. 11/4:00). Dates/Times which are already taken: "
                + ", ".join(dates)
            )
            response = await self.bot.wait_for("message", timeout=90, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The promo submission process has stopped.")
                return
            new_date = response.content.split("/")
            new_promo.extend(new_date)
            await ctx.send(
                "Member ID(s) (in the format 'number_1 number_2' etc. without any commas or <@!, >):"
            )
            response = await self.bot.wait_for("message", timeout=90, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The promo submission process has stopped.")
                return
            new_promo.append(
                " ".join([f"<@!{id}>" for id in response.content.split(" ") if id])
            )

            new_promo_msg, mode = promo_make(new_promo)
            await ctx.send(
                f"The new promo will appear every {new_date[0]} {ordinal(int(new_date[0]))} "
                f"day of each month at {new_date[1]} as follows:"
            )
            if mode == "embed":
                await ctx.send(embed=new_promo_msg)
            else:
                await ctx.send(new_promo_msg)

            await ctx.send("Do you want to submit (y/n)?")
            confirm = await self.bot.wait_for("message", timeout=30, check=check)
            if confirm.content.lower().startswith("y"):
                PROMOS_WKS.append_row(new_promo)
                await ctx.send("The promo was submitted.")
            elif confirm.content.lower().startswith("n"):
                await ctx.send("The promo was not submitted.")
            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    "Please start the promo submission process again."
                )
                return

        except TimeoutError:
            await ctx.send("Time has run out.")
        except:
            await ctx.send("Something went wrong. Please try again.")

    @tasks.loop(minutes=60)
    async def ads_loop(self):
        time_now = pendulum.now("America/Toronto")
        print(
            "Promotions loop is working ("
            + time_now.strftime("%Y-%m-%d, %H:%M:%S EST")
            + ")."
        )
        promos = PROMOS_WKS.get_all_values()[1:]
        for promo in promos:
            promo = [remove_spaces(i) for i in promo]
            promo[5] = promo[5].split(":")[0]
            if promo[4].lower().startswith("last"):
                promo[4] = time_now._last_of_month().day
            if time_now.day == int(promo[4]) and time_now.hour == int(promo[5]):
                guild = self.bot.get_guild(SERVER)
                if promo[6] != "N/A":
                    try:
                        for member_id in promo[6].split(" "):
                            await guild.fetch_member(
                                int(remove_spaces(member_id)[3:-1])
                            )
                        post_in_channel = PROMOS_CHANNEL
                    except:
                        post_in_channel = REJECTED_PROMOS_CHANNEL
                        await self.bot.get_channel(REJECTED_PROMOS_CHANNEL).send(
                            "The following promo will not be posted because I can't "
                            "find at least one of its related members in the server:"
                        )
                    promo_msg, mode = promo_make(promo)
                    if mode == "embed":
                        await self.bot.get_channel(post_in_channel).send(
                            embed=promo_msg
                        )
                    else:
                        await self.bot.get_channel(post_in_channel).send(promo_msg)
                else:
                    await self.bot.get_channel(PROMOS_CHANNEL).send(
                        f"**{promo[2]}**\n\n{promo[3]}"
                    )


def promo_make(promo):
    if promo[1].lower().startswith("y"):
        embed = Embed(color=Color.blue())
        posts = post_split(f"{promo[6]}\n\n{promo[3]}", 1024)
        for i in range(len(posts)):
            if i == 0:
                embed.add_field(name=promo[2], value=posts[0], inline=False)
            else:
                embed.add_field(name="\u200b", value=posts[i], inline=False)
        return embed, "embed"
    else:
        return f"**{promo[2]}**\n\n{promo[3]}", "no embed"


# Add cog to bot
def setup(bot):
    bot.add_cog(Promotions(bot))
