# Discord
import discord
from discord.ext import commands

# Libraries to load tokens
from os import getenv, listdir

# Libraries for various functions
import pendulum
import chat_exporter
import io

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

    @commands.command(
        brief="Archive a channel from its channel id.",
        description="Archive a channel from its channel id "
        "(e.g. ,archive 123456789012345678).",
    )
    async def archive(self, ctx, channel_id=None):
        if channel_id == None:
            await ctx.send("Please specify a valid channel id.")
            return

        try:
            channel = self.bot.get_channel(int(channel_id))
        except:
            await ctx.send("Please specify a valid channel id.")
            return

        transcript = await chat_exporter.export(channel, set_timezone="America/Toronto")
        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"{channel.name}.html",
        )

        await ctx.send(file=transcript_file)


bot.add_cog(General(bot))


# Run bot
bot.run(getenv("TOKEN"))
