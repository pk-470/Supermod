from discord.ext.commands import Bot

from .qotd import QOTD


async def setup(bot: Bot):
    await bot.add_cog(QOTD(bot))
