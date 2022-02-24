# Discord
from discord.ext import commands

# Libraries to load tokens
from os import getenv, listdir

# Libraries for various functions
import pendulum

# Connect to Discord and define prefix
bot = commands.Bot(command_prefix=",", case_insensitive=True)

# --------------------------------------------------MODE-SWITCH--------------------------------------------------
# Choose the mode (ON to run the bot locally, OFF to upload and run on Heroku)
local_mode = "OFF"
# --------------------------------------------------MODE-SWITCH--------------------------------------------------

with open("mode_switch.txt", "w") as switch:
    switch.write(local_mode)

if local_mode == "ON":
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
    print("I am logged in as {0.user}.".format(bot))
    # Load all features
    for feature in features:
        bot.load_extension("features." + feature)
        print(
            "Feature "
            + feature
            + " has been loaded ("
            + pendulum.now().strftime("%Y-%m-%d, %H:%M:%S")
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
