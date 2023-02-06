from discord.ext.commands import Bot
from features.promotions.promotions import Promotions


async def setup(bot: Bot):
    await bot.add_cog(Promotions(bot))
