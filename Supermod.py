from discord import Intents
from discord.ext.commands import Bot
import os

from utils import *

intents = Intents.all()
bot = Bot(command_prefix=",", case_insensitive=True, intents=intents)


async def load_features():
    features = [filename for filename in os.listdir("./features") if filename[0] != "_"]
    for feature in features:
        await bot.load_extension(f"features.{feature}")
        print_info(f"Feature {feature} has been loaded.")


@bot.event
async def on_ready():
    print_info(f"I am logged in as {bot.user}.")
    await load_features()


def run_bot(LOCAL_MODE):
    print_info(f"Starting Supermod (LOCAL_MODE: {LOCAL_MODE}).")

    with open("mode_switch/mode_switch.txt", "w") as switch:
        switch.write(LOCAL_MODE)

    from mode_switch import mode_setup

    mode_setup()

    bot.run(os.getenv("TOKEN"))


if __name__ == "__main__":
    run_bot(LOCAL_MODE="OFF")
