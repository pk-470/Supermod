from discord.ext.commands import Bot

from .newsletter import Newsletter


async def setup(bot: Bot):
    await bot.add_cog(Newsletter(bot))
