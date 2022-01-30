# Library for discord
from discord.ext import tasks, commands

# Library for API handling
import gspread

# Libraries to load hidden data from .env
from os import getenv
from dotenv import load_dotenv

# Import newsletter functions
import releases

# Libraries for various functions
from random import choice
import pendulum

# Connect to Discord and define prefix
bot = commands.Bot(command_prefix=".")

# Connect to Google service account
gsa = gspread.service_account()

# Load hidden data from .env
load_dotenv()

# Testing channel
bot.channel = int(getenv("TESTING_CHANNEL"))


# on_ready
@bot.event
async def on_ready():
    print("I am logged in as {0.user}.".format(bot))
    qotd.start()
    weekly_newsletter.start()


# General commands
@bot.command()
async def hello(ctx):
    await ctx.send("It's alright. Why? Because I am here!")


# QOTD

# Setting
bot.qotd_channel = bot.channel
bot.qotd_hour = 22
qotd_wks = gsa.open_by_url(getenv("QOTD_SHEET_URL")).sheet1


# Commands
@bot.command()
async def qotd_set(ctx, qotd_hour):
    try:
        qotd_hour = int(qotd_hour)
        if qotd_hour < 0 or qotd_hour > 23:
            await ctx.send("Please provide a valid hour.")
        else:
            bot.qotd_hour = qotd_hour
    except:
        await ctx.send("Please provide a valid hour.")


@bot.command()
async def qotd_time(ctx):
    await ctx.send(bot.qotd_hour)


@bot.command()
async def qotd(ctx):
    await ctx.send(qotd_get())


# Fetching questions
def qotd_get():
    questions = qotd_wks.get_values()
    question = choice(questions)
    return question[0].strip("'")


# QOTD loop
@tasks.loop(minutes=60)
async def qotd():
    print(
        "QOTD loop is working (time: "
        + pendulum.now().strftime("%Y-%m-%d, %H:%M:%S")
        + ")."
    )
    if pendulum.now().hour == bot.qotd_hour:
        print(
            "QOTD has been posted (date: " + pendulum.now().strftime("%Y-%m-%d") + ")."
        )
        channel = bot.get_channel(bot.qotd_channel)
        await channel.send(qotd_get())


# NEWSLETTER

# Setting
bot.news_channel = bot.channel
bot.news_day = "Monday"
news_sh = gsa.open_by_url(getenv("NEWS_SHEET_URL"))


# Commands
@bot.command()
async def news_set(ctx, news_day):
    days = (
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    )
    if not news_day in days:
        await ctx.send("Please provide a valid day of the week.")
    else:
        bot.news_day = news_day


@bot.command()
async def news_day(ctx):
    await ctx.send(bot.news_day)


@bot.command()
async def news(ctx, date_str=None):
    if date_str == None:
        date = pendulum.today()
    else:
        try:
            date = pendulum.from_format(date_str, "M/D/YYYY")
            if date.year < 2021:
                await ctx.send(
                    "The OL Newsletter only contains albums released in 2021 or later."
                )
                return
        except:
            await ctx.send(
                "Please make sure your date is in the correct format (M/D/YYYY)."
            )
            return

    sheet = str(date.year) + " OL Rock Albums List"
    sheet_data = news_sh.worksheet(sheet).get_all_values()
    posts = releases.newsletter_create(sheet_data, date)
    for post in posts:
        await ctx.send(post)


@bot.command()
async def news_full(ctx, *, message=None):
    if message == None:
        await ctx.send("What will be this week's newsletter message?")
        return
    else:
        date = pendulum.today()
        sheet_data = news_sh.sheet1.get_all_values()
        posts = releases.newsletter_create(sheet_data, date, message)
        for post in posts:
            await ctx.send(post)


# Newsletter loop
@tasks.loop(hours=24)
async def weekly_newsletter():
    print(
        "Newsletter loop is working (date: "
        + pendulum.now().strftime("%Y-%m-%d")
        + ")."
    )
    if pendulum.now().strftime("%A") == bot.news_day:
        channel = bot.get_channel(bot.news_channel)
        date = pendulum.today()
        sheet_data = news_sh.sheet1.get_all_values()
        posts = releases.newsletter_create(sheet_data, date)
        for post in posts:
            await channel.send(post)
        print(
            "Newsletter has been sent (day: "
            + pendulum.now().strftime("%A, %Y-%m-%d")
            + ")."
        )


bot.run(getenv("TOKEN"))
