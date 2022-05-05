# Discord
from discord.ext import commands

# Libraries to load tokens
from os import getenv, listdir

# Libraries for various functions
import pendulum

# Connect to Discord and define prefix
bot = commands.Bot(command_prefix=",", case_insensitive=True)

# ------------------------------------------------------MODE-SWITCH------------------------------------------------------
# Choose the local mode (ON to run the bot locally, OFF to upload and run on Heroku).
LOCAL_MODE = "OFF"
# ----------------------------------------------------MODE-SWITCH-END----------------------------------------------------

with open("mode_switch.txt", "w") as switch:
    switch.write(LOCAL_MODE)

if LOCAL_MODE == "ON":
    from dotenv import load_dotenv

    load_dotenv("tokens/.env")

# Features to be loaded
features = [
    filename[:-3]
    for filename in listdir("./features")
    if filename.endswith(".py") and filename != "__init__.py"
]

# On ready
@bot.event
async def on_ready():
    print(f"I am logged in as {bot.user}.")
    # Load all features
    for feature in features:
        bot.load_extension(f"features.{feature}")
        print(
            f"Feature {feature} has been loaded ("
            + pendulum.now("America/Toronto").strftime("%Y-%m-%d, %H:%M:%S EST")
            + ")."
        )


# General commands
class General(commands.Cog, description="General commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        brief="The All Might Supermod appears.",
        description="The All Might Supermod appears.",
    )
    async def hello(self, ctx):
        await ctx.send("It's fine now. Why? Because I am here!")


bot.add_cog(General(bot))


# Run bot
bot.run(getenv("TOKEN"))
