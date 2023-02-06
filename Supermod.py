from discord import Intents
from discord.ext.commands import Bot
import os
import pendulum

from mode_switch import mode_setup


intents = Intents.all()
bot = Bot(command_prefix=",", case_insensitive=True, intents=intents)


async def load_features():
    features = [filename for filename in os.listdir("./features") if filename[0] != "_"]
    for feature in features:
        await bot.load_extension(f"features.{feature}")
        print(
            f"{pendulum.now('America/Toronto').strftime('%Y-%m-%d %H:%M:%S EST')}: "
            f"Feature {feature} has been loaded "
        )


@bot.event
async def on_ready():
    print(
        f"{pendulum.now('America/Toronto').strftime('%Y-%m-%d %H:%M:%S EST')}: "
        f"I am logged in as {bot.user}."
    )
    await load_features()


def run_bot(LOCAL_MODE):

    with open("mode_switch/mode_switch.txt", "w") as switch:
        switch.write(LOCAL_MODE)

    mode_setup()
    bot.run(os.getenv("TOKEN"))


if __name__ == "__main__":
    run_bot(LOCAL_MODE="OFF")
