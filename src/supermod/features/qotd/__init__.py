from discord.ext.commands import Bot

from supermod.features.qotd.qotd import QOTD


async def setup(bot: Bot):
    await bot.add_cog(QOTD(bot))
