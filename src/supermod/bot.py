import logging
import pkgutil

from discord import AllowedMentions, Intents
from discord.ext import commands
from discord.ext.commands import Bot, Context

from supermod._logging import setup_logging
from supermod._mode_setup import is_local, mode_setup
from supermod._paths import FEATURES_DIR, FEATURES_PACKAGE
from supermod._utils import get_and_verify_env

logger = logging.getLogger(__name__)


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
        logger.info("Logged in as %s.", self.user)

    async def on_command(self, ctx: Context) -> None:
        logger.info(
            "Command '%s' invoked by %s (%s) in #%s.",
            ctx.command,
            ctx.author,
            ctx.author.id,
            ctx.channel,
        )

    async def on_command_completion(self, ctx: Context) -> None:
        logger.info("Command '%s' completed for %s.", ctx.command, ctx.author)

    async def on_command_error(
        self, ctx: Context, error: commands.CommandError
    ) -> None:
        # An unknown command is not worth a reply or a log line.
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CheckFailure):
            logger.info(
                "Command '%s' denied for %s (failed checks).", ctx.command, ctx.author
            )
            await ctx.send("You don't have permission to use this command.")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            logger.info(
                "Command '%s' by %s missing argument '%s'.",
                ctx.command,
                ctx.author,
                error.param.name,
            )
            await ctx.send(f"Missing required argument: {error.param.name}.")
            return
        # Unwrap CommandInvokeError so the log carries the underlying cause.
        original = getattr(error, "original", error)
        logger.error(
            "Unhandled error in command %s.",
            getattr(ctx.command, "qualified_name", "<unknown>"),
            exc_info=original,
        )
        if ctx.command is not None:
            await ctx.send(
                f"Something went wrong while running `{ctx.command.qualified_name}`. "
                "The error has been logged for the staff to look into."
            )
        else:
            await ctx.send(
                "Something went wrong. The error has been logged for the staff to "
                "look into."
            )

    async def load_features(self) -> None:
        for module in pkgutil.iter_modules([str(FEATURES_DIR)]):
            if module.name.startswith("_"):
                continue
            try:
                await self.load_extension(f"{FEATURES_PACKAGE}.{module.name}")
                logger.info("Feature %s has been loaded.", module.name)
            except Exception:
                logger.exception("Failed to load feature %s.", module.name)

    def run_bot(self) -> None:
        setup_logging()
        logger.info("Starting Supermod (local mode: %s).", is_local())

        # Authenticate now so that, in local mode, load_dotenv populates TOKEN
        # (and the other secrets) before they are read below.
        mode_setup()

        token = get_and_verify_env("TOKEN")
        self.run(token, log_handler=None)
