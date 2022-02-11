# Library for Discord
from discord.ext import commands

# Import submission class
from classes.submission_class import submission

# Import post_split
from features.releases import post_split

# Library to load tokens
from os import getenv

# Libraries for various functions
import asyncio

# Import data according to local_mode status
local_mode = open("mode_switch.txt", "r").read()

if local_mode == "ON":
    from dotenv import load_dotenv

    load_dotenv("tokens/.env")


# Setting
submissions_channel = int(getenv("SUBMISSIONS_CHANNEL"))
voted_channel = int(getenv("VOTED_CHANNEL"))
new_channel = int(getenv("NEW_CHANNEL"))
modern_channel = int(getenv("MODERN_CHANNEL"))
classic_channel = int(getenv("CLASSIC_CHANNEL"))
theme_channel = int(getenv("THEME_CHANNEL"))

channels_dict = {
    "voted": voted_channel,
    "new": new_channel,
    "modern": modern_channel,
    "classic": classic_channel,
    "theme": theme_channel,
}


class Album_Submissions(
    commands.Cog,
    name="Album Submissions",
    description="Functions to handle album submissions for the masterlists.",
):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def subs(self, ctx, masterlist=None):
        # Check if an appropriate masterlist is chosen, otherwise prompt for one.
        if masterlist == None or masterlist.lower() in (
            "voted",
            "new",
            "modern",
            "classic",
            "theme",
            "error",
        ):
            msgs = []
            # Fetch submission history and keep those with no reaction.
            async for msg in self.bot.get_channel(submissions_channel).history(
                oldest_first=True
            ):
                if not msg.reactions:
                    msgs.append(msg)
            # Check if there are new submissions, and if so create the mod approval message.
            subs_dict = masterlist_dict(msgs, masterlist)
            if subs_dict:
                check_list = []
                for item in list(subs_dict.items()):
                    if item[1][0] != None:
                        check_list.append(
                            "**" + item[0] + ".** " + item[1][0].sub_check_msg_full()
                        )
                    else:
                        check_list.append(
                            "**"
                            + item[0]
                            + ".** "
                            + "Something went wrong with submission "
                            + item[1][1].jump_url
                        )
                subs_check_msg_full = "\n".join(check_list)
                subs_check = post_split(subs_check_msg_full, 2000)
                for sub_check in subs_check:
                    await ctx.send(sub_check)
            else:
                if masterlist == None:
                    await ctx.send("There are no new submissions.")
                elif masterlist == "error":
                    await ctx.send("There are no new submissions with errors.")
                else:
                    await ctx.send(
                        "There are no new submissions for the "
                        + masterlist.upper()
                        + " masterlist."
                    )

                return

            # Submission checking options.

            def check(resp):
                return resp.author == ctx.author

            try:
                response = await self.bot.wait_for(
                    "message", timeout=600.0, check=check
                )

                # Approve submissions
                if response.content.lower().startswith("ok"):
                    if masterlist == "error":
                        await ctx.send(
                            "I can't add submissions with errors to the masterlist."
                        )
                    elif masterlist == None:
                        for item in list(subs_dict.items()):
                            if item[1][0] != None:
                                await self.bot.get_channel(
                                    channels_dict[item[1][0].masterlist]
                                ).send(item[1][0].masterlist_format())
                                await item[1][1].add_reaction("🆗")
                        await ctx.send(
                            "All new submissions without errors were added to the masterlists."
                        )
                    else:
                        for item in list(subs_dict.items()):
                            if (
                                item[1][0] != None
                                and item[1][0].masterlist == masterlist
                            ):
                                await self.bot.get_channel(
                                    channels_dict[item[1][0].masterlist]
                                ).send(item[1][0].masterlist_format())
                        await ctx.send(
                            "All new submissions without errors were added to the "
                            + masterlist.upper()
                            + " masterlist."
                        )

                # Reject and delete submissions
                elif response.content.lower().startswith("reject"):
                    sub_nos = [no for no in response.content if no.isnumeric()]
                    sub_msgs = [subs_dict[no][1] for no in sub_nos]
                    if len(sub_nos) == 1:
                        await ctx.send(
                            "Are you sure you want to reject album "
                            + sub_nos[0]
                            + " (y/n)?"
                        )
                    elif len(sub_nos) > 1:
                        await ctx.send(
                            "Are you sure you want to reject albums "
                            + ", ".join(sub_nos)
                            + " (y/n)?"
                        )

                    # Confirm rejection
                    def check(conf):
                        return conf.author == ctx.author and conf.channel == ctx.channel

                    confirm = await self.bot.wait_for(
                        "message", timeout=30.0, check=check
                    )
                    if confirm.content.lower().startswith("y"):
                        for msg in sub_msgs:
                            await msg.delete()
                        if len(sub_nos) == 1:
                            await ctx.send("Album " + sub_nos[0] + " was rejected.")
                        elif len(sub_nos) > 1:
                            await ctx.send(
                                "Albums " + ", ".join(sub_nos) + " were rejected."
                            )
                    else:
                        if len(sub_nos) == 1:
                            await ctx.send("Album " + sub_nos[0] + " was not rejected.")
                        elif len(sub_nos) > 1:
                            await ctx.send(
                                "Albums " + ", ".join(sub_nos) + " were not rejected."
                            )
            except asyncio.TimeoutError:
                await ctx.send("Time has run out.")
        else:
            await ctx.send(
                "Please provide a valid masterlist, or 'error' if you want to fetch all"
                + " new submissions with errors, or no masterlist if you want to fetch all"
                + " new submissions from all lists (including those with errors)."
            )


def submission_make(msg):
    # Input a Discord message (NOT a string).
    # Returns a submission or None if things go wrong.
    sub_message = msg.content
    request = "add"
    if sub_message.lower().startswith("replace"):
        request = "replace"
        sub_message = sub_message[sub_message.lower().find("with") + 4 :]
    if sub_message[0] == ":":
        sub_message = sub_message[1:]

    sub_data = sub_message.split("//")

    try:
        sub_album = submission(
            artists=sub_data[1],
            title=sub_data[0],
            genres=sub_data[3],
            release_date=sub_data[2],
            submitter_name=msg.author.name,
            submitter_id=msg.author.id,
            masterlist=sub_data[4],
            request=request,
        )
    except:
        return None

    return sub_album


def masterlist_dict(msgs, masterlist=None):
    # Input a list of Discord messages (NOT strings).
    # Returns a dictionary in the form {str(int), [submission, sub msg]}
    # consisting of all submissions for the chosen masterlist.
    subs_dict = {}
    entry = 1
    for msg in msgs:
        sub_album = submission_make(msg)
        if masterlist == None:
            subs_dict[str(entry)] = (sub_album, msg)
            entry = entry + 1
        elif masterlist == "error" and sub_album == None:
            subs_dict[str(entry)] = (None, msg)
            entry = entry + 1
        elif sub_album != None and sub_album.masterlist == masterlist:
            subs_dict[str(entry)] = (sub_album, msg)
            entry = entry + 1

    return subs_dict


# Add cog to bot
def setup(bot):
    bot.add_cog(Album_Submissions(bot))
