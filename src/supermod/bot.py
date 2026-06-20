import pkgutil

from discord import AllowedMentions, Intents
from discord.ext.commands import Bot

from supermod._mode_setup import is_local, mode_setup
from supermod._paths import FEATURES_DIR, FEATURES_PACKAGE
from supermod._utils import get_and_verify_env, print_info


class Supermod(Bot):
    def __init__(self):
        intents = Intents.all()
        super().__init__(
            command_prefix=",",
            case_insensitive=True,
            intents=intents,
            allowed_mentions=AllowedMentions.none(),
        )

    async def setup_hook(self) -> None:
        # Runs exactly once, before the gateway connects — the idiomatic place
        # for async startup. (on_ready can fire again on every reconnect, which
        # would re-load every extension and raise ExtensionAlreadyLoaded.)
        await self.load_features()

    async def on_ready(self) -> None:
        print_info(f"I am logged in as {self.user}.")

    async def load_features(self) -> None:
        for module in pkgutil.iter_modules([str(FEATURES_DIR)]):
            if module.name.startswith("_"):
                continue
            try:
                await self.load_extension(f"{FEATURES_PACKAGE}.{module.name}")
                print_info(f"Feature {module.name} has been loaded.")
            except Exception as e:
                print_info(
                    f"Failed to load feature {module.name}: {type(e).__name__}: {e}"
                )

    def run_bot(self) -> None:
        print_info(f"Starting Supermod (local mode: {is_local()}).")

        # Authenticate now so that, in local mode, load_dotenv populates TOKEN
        # (and the other secrets) before they are read below.
        mode_setup()

        token = get_and_verify_env("TOKEN")
        self.run(token)
