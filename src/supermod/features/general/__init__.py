from discord.ext.commands import Bot

from supermod.features.general.general import General


async def setup(bot: Bot):
    await bot.add_cog(General(bot))
