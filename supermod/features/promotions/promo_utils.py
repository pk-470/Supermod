from discord import Colour, Embed, Message, TextChannel
from discord.ext.commands import Bot, Context

from ..newsletter.news_utils import ordinal, post_split
from .promo_constants import *


def promo_make(promo_data: list[str]) -> Embed | str:
    """
    Make the formatted message for the promo from the promo data (list).
    """
    # Embed
    if promo_data[1].lower().startswith("y"):
        embed = Embed(color=Colour.blue())
        posts = post_split(f"{promo_data[6]}\n\n{promo_data[3]}", 1024)
        for i, post in enumerate(posts):
            if i == 0:
                embed.add_field(name=promo_data[2], value=post, inline=False)
            else:
                embed.add_field(name="\u200b", value=post, inline=False)
        return embed
    # No embed
    else:
        return f"**{promo_data[2]}**\n\n{promo_data[3]}"


async def promo_post(
    promo_formatted: Embed | str, channel: TextChannel | Context
) -> None:
    """
    Post a promo in a channel.
    """
    # Embed
    if isinstance(promo_formatted, Embed):
        await channel.send(embed=promo_formatted)
    # No embed
    elif isinstance(promo_formatted, str):
        await channel.send(promo_formatted)


async def promo_add_interaction(bot: Bot, ctx: Context) -> None:
    dates = [f"{promo[4]}/{promo[5]}" for promo in PROMOS_WKS.get_all_values()[1:]]
    new_promo_data = []

    def check(resp: Message):
        return resp.author == ctx.author and resp.channel == ctx.channel

    # Starting message
    await ctx.send("Respond with 'stop' at any point to stop the process.")

    # Submitter type (creator / partner)
    await ctx.send("Submitter Type (Creator / Partner):")
    response = await bot.wait_for("message", timeout=30, check=check)
    if response.content.lower() == "stop":
        await ctx.send("The promo submission process has stopped.")
        return
    if response.content.lower()[0] == "c":
        embed = "Yes"
    elif response.content.lower()[0] == "p":
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
    response = await bot.wait_for("message", timeout=30, check=check)
    if response.content.lower() == "stop":
        await ctx.send("The promo submission process has stopped.")
        return
    new_promo_data.append(response.content.capitalize())

    # Promo content
    await ctx.send("Message (no mentions on top):")
    response = await bot.wait_for("message", timeout=90, check=check)
    if response.content.lower() == "stop":
        await ctx.send("The promo submission process has stopped.")
        return
    new_promo_data.append(response.content)

    # Choose date/time
    await ctx.send(
        "Date/Time (e.g. 11/4:00). Dates/Times which are already taken: "
        + ", ".join(dates)
    )
    response = await bot.wait_for("message", timeout=90, check=check)
    if response.content.lower() == "stop":
        await ctx.send("The promo submission process has stopped.")
        return
    new_date = response.content.split("/")
    new_promo_data.extend(new_date)

    # Member ID(s)
    await ctx.send(
        "Member ID(s) (in the format 'number_1 number_2' etc. without any commas or <@!, >):"
    )
    response = await bot.wait_for("message", timeout=90, check=check)
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
    await promo_post(new_promo_formatted, ctx)

    # Ask for approval
    await ctx.send("Do you want to submit (y/n)?")
    confirm = await bot.wait_for("message", timeout=30, check=check)
    if confirm.content.lower().startswith("y"):
        PROMOS_WKS.append_row(new_promo_data)
        await ctx.send("The promo was submitted.")
    elif confirm.content.lower().startswith("n"):
        await ctx.send("The promo was rejected.")
    else:
        await ctx.send(
            f"I don't know what you mean by '{response.content}'. "
            + "Please start the promo submission process again."
        )
        return
