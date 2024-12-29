import os

from discord import Intents
from discord.ext.commands import Bot

from .paths import *
from .utils import *

intents = Intents.all()
bot = Bot(command_prefix=",", case_insensitive=True, intents=intents)


async def load_features():
    features = [
        filename for filename in os.listdir(FEATURES_PATH) if filename[0] != "_"
    ]
    for feature in features:
        await bot.load_extension(f"supermod.features.{feature}")
        print_info(f"Feature {feature} has been loaded.")


@bot.event
async def on_ready():
    print_info(f"I am logged in as {bot.user}.")
    await load_features()


def run_bot(LOCAL_MODE: str):
    print_info(f"Starting Supermod (LOCAL_MODE: {LOCAL_MODE}).")

    with open(MODE_SWITCH_PATH, "w", encoding="utf-8") as switch:
        switch.write(LOCAL_MODE)

    from supermod.mode_switch import mode_setup

    mode_setup()

    token = os.getenv("TOKEN")
    assert token is not None
    bot.run(token)
