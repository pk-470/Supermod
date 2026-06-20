from discord.ext.commands import Bot

from supermod.features.submissions.submissions import Submissions


async def setup(bot: Bot):
    await bot.add_cog(Submissions(bot))
