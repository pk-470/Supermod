from discord.ext.commands import Bot
from features.submissions_status.submissions_status import Submissions_Status


async def setup(bot: Bot):
    await bot.add_cog(Submissions_Status(bot))
