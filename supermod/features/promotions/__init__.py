from discord.ext.commands import Bot

from .promotions import Promotions


async def setup(bot: Bot):
    await bot.add_cog(Promotions(bot))
