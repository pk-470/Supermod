# pylint: disable=redefined-outer-name,import-outside-toplevel

import os

from discord import Intents
from discord.ext.commands import Bot

from .paths import *
from .utils import *


class Supermod(Bot):
    def __init__(self, intents: Intents):
        super().__init__(command_prefix=",", case_insensitive=True, intents=intents)

    async def load_features(self) -> None:
        features = [
            filename for filename in os.listdir(FEATURES_PATH) if filename[0] != "_"
        ]
        for feature in features:
            await self.load_extension(f".features.{feature}")
            print_info(f"Feature {feature} has been loaded.")

    def run_bot(self, LOCAL_MODE: str):
        print_info(f"Starting Supermod (LOCAL_MODE: {LOCAL_MODE}).")

        with open(MODE_SWITCH_PATH, "w", encoding="utf-8") as switch:
            switch.write(LOCAL_MODE)

        from .mode_switch import mode_setup

        mode_setup()

        token = os.getenv("TOKEN")
        assert token is not None
        self.run(token)
