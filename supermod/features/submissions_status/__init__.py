from discord.ext.commands import Bot

from .submissions_status import SubmissionsStatus


async def setup(bot: Bot):
    await bot.add_cog(SubmissionsStatus(bot))
