from discord import Intents

from supermod import Supermod
from supermod.utils import print_info

intents = Intents.all()
SUPERMOD = Supermod(intents)


@SUPERMOD.event
async def on_ready():
    print_info(f"I am logged in as {SUPERMOD.user}.")
    await SUPERMOD.load_features()


if __name__ == "__main__":
    SUPERMOD.run_bot(LOCAL_MODE="OFF")
