from supermod import Supermod
from supermod.utils import print_info

SUPERMOD = Supermod()


@SUPERMOD.event
async def on_ready():
    print_info(f"I am logged in as {SUPERMOD.user}.")
    await SUPERMOD.load_features()


if __name__ == "__main__":
    SUPERMOD.run_bot(LOCAL_MODE="OFF")
