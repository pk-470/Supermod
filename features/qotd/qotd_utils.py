from discord import Reaction, User
from discord.ext.commands import Bot, Context
import pendulum
from random import choice

from utils import *
from features.qotd.qotd_constants import *


async def qotd_interact(bot: Bot, ctx: Context, timeout):
    question = qotd_get()
    qotd = await ctx.send(question[2])
    await qotd.add_reaction("✅")
    await qotd.add_reaction("❌")
    await qotd.add_reaction("🇪")

    def check(reaction: Reaction, user: User):
        return str(reaction.emoji) in ("✅", "❌", "🇪") and user != bot.user

    try:
        reaction, user = await bot.wait_for(
            "reaction_add", timeout=timeout, check=check
        )
        if str(reaction.emoji) == "✅":
            await qotd_post(question, bot, ctx)
        elif str(reaction.emoji) == "❌":
            await ctx.send("The QOTD was rejected.")
        elif str(reaction.emoji) == "🇪":
            await ctx.send(
                f"Respond with an edited version of the {question[0].lower()} "
                f"which I will post instead (I will mark the original {question[0].lower()} "
                "as used in the spreadsheet without changing its template). "
                "Respond with 'stop' if you want me to stop waiting for a response."
            )

            def check(response):
                return response.author == user

            response = await bot.wait_for("message", timeout=600, check=check)
            if response.content.lower() == "stop":
                await ctx.send("The QOTD editing process has stopped.")
                return
            await ctx.send("The following will be posted as QOTD:")
            qotd = await ctx.send(response.content)
            await qotd.add_reaction("✅")
            await qotd.add_reaction("❌")

            def check(reaction, user):
                return str(reaction.emoji) in ("✅", "❌") and user != bot.user

            reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
            if str(reaction.emoji) == "✅":
                await qotd_post(question, bot, ctx, overwrite=response.content)
            elif str(reaction.emoji) == "❌":
                await ctx.send("The QOTD was rejected.")

    except TimeoutError:
        await ctx.send("Time has run out.")


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


async def qotd_post(question, bot: Bot, ctx: Context, overwrite=None):
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
    print_info(conf_msg)
    await ctx.send(conf_msg)
