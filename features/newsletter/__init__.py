from discord.ext.commands import Bot
from features.newsletter.newsletter import Newsletter


async def setup(bot: Bot):
    await bot.add_cog(Newsletter(bot))
