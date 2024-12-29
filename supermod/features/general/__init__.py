from discord.ext.commands import Bot

from .general import General


async def setup(bot: Bot):
    await bot.add_cog(General(bot))
