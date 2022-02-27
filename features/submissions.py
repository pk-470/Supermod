# Library for Discord
from discord.ext import commands

# Google spreadsheets
import gspread

# Import submission class
from classes.submission_class import Submission, Sub_error

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

    gsa = gspread.service_account("tokens/service_account.json")
else:
    from json import loads

    gsa = gspread.service_account_from_dict(loads(getenv("SERVICE_ACCOUNT_CRED")))


# Setting
albums_wks = gsa.open_by_url(getenv("ALBUMS_SHEET_URL")).sheet1
weeks_wks = gsa.open_by_url(getenv("ALBUMS_SHEET_URL")).get_worksheet(1)

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

    @commands.command(
        brief="Fetch and approve or reject submissions for the masterlists.",
        description="Optional argument: masterlist name (i.e. one of 'voted', 'new', 'modern',"
        + " 'classic', 'theme') to only fetch submissions for that masterlist, or 'error' to fetch"
        + " messages in #submissions which cannot be correctly interpreted as a submission by the bot."
        + " Once the submissions have been fetched, you have 20 minutes to respond with 'ok' in order"
        + " to approve all submissions, 'reject' followed by the numbers of the submissions you want to"
        + " reject, or 'stop' to stop the process.",
    )
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
            subs_dict = await subs_check_msg(ctx, self.bot, masterlist)
            if not subs_dict:
                return

            await ctx.send(
                "You have 20 minutes to respond with 'ok' in order to approve all"
                + " submissions, 'reject' followed by the numbers of the submissions"
                + " you want to reject, or 'stop' to stop the process."
            )

            # Submission checking options

            def check(resp):
                return resp.author == ctx.author and resp.channel == ctx.channel

            try:
                response = await self.bot.wait_for(
                    "message", timeout=1200.0, check=check
                )

                if response.content.lower().startswith("stop"):
                    await ctx.send("The submissions approval process has stopped.")
                    return

                # Approve submissions
                elif response.content.lower().startswith("ok"):
                    if masterlist == "error":
                        await ctx.send(
                            "I can't add submissions with errors to the masterlist."
                        )
                    elif masterlist == None:
                        for _, sub in list(subs_dict.items()):
                            if type(sub).__name__ != "Sub_error":
                                await self.bot.get_channel(
                                    channels_dict[sub.masterlist]
                                ).send(sub.masterlist_format())
                                await sub.message.add_reaction("🆗")
                        await ctx.send(
                            "All new submissions without errors were added to the masterlists."
                        )
                    else:
                        for _, sub in list(subs_dict.items()):
                            if (
                                type(sub).__name__ != "Sub_error"
                                and sub.masterlist == masterlist
                            ):
                                await self.bot.get_channel(
                                    channels_dict[sub.masterlist]
                                ).send(sub.masterlist_format())
                        await ctx.send(
                            "All new submissions without errors were added to the "
                            + masterlist.upper()
                            + " masterlist."
                        )

                # Reject and delete submissions
                elif response.content.lower().startswith("reject"):
                    resp_content = response.content.split(" ")
                    sub_indices = []
                    for ind in resp_content:
                        if ind[-1] == ",":
                            ind = ind[:-1]
                        try:
                            int(ind)
                            sub_indices.append(ind)
                        except:
                            pass
                    sub_msgs = [subs_dict[ind].message for ind in sub_indices]
                    if len(sub_indices) == 1:
                        await ctx.send(
                            "Are you sure you want to reject album "
                            + sub_indices[0]
                            + " (y/n)?"
                        )
                    elif len(sub_indices) > 1:
                        await ctx.send(
                            "Are you sure you want to reject albums "
                            + ", ".join(sub_indices)
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
                        if len(sub_indices) == 1:
                            await ctx.send("Album " + sub_indices[0] + " was rejected.")
                        elif len(sub_indices) > 1:
                            await ctx.send(
                                "Albums " + ", ".join(sub_indices) + " were rejected."
                            )
                    else:
                        if len(sub_indices) == 1:
                            await ctx.send(
                                "Album " + sub_indices[0] + " was not rejected."
                            )
                        elif len(sub_indices) > 1:
                            await ctx.send(
                                "Albums "
                                + ", ".join(sub_indices)
                                + " were not rejected."
                            )
                else:
                    await ctx.send(
                        "I don't know what you mean by '"
                        + response.content
                        + "'. Please start the submissions approval process again."
                    )
                return

            except asyncio.TimeoutError:
                await ctx.send("Time has run out.")
            except:
                await ctx.send("Something went wrong. Please try again.")

        else:
            await ctx.send(
                "Please provide a valid masterlist, or 'error' if you want to fetch all"
                + " new submissions with errors, or no masterlist if you want to fetch all"
                + " new submissions from all lists (including those with errors)."
            )


def submission_make(msg):
    # Input a Discord message (NOT A STRING).
    # Returns a Submission class if things go right or
    # a Sub_error class if things go wrong.
    try:
        sub_message = msg.content
        request = "add"
        if sub_message.lower().startswith("replace"):
            request = "replace"
            sub_message = sub_message[sub_message.lower().find("with") + 4 :]
        if sub_message[0] == ":":
            sub_message = sub_message[1:]

        sub_data = sub_message.split("//")
        sub_album = Submission(
            artist=sub_data[1],
            title=sub_data[0],
            genres=sub_data[3],
            release_date=sub_data[2],
            submitter_name=msg.author.display_name,
            submitter_id=msg.author.id,
            masterlist=sub_data[4],
            message=msg,
            request=request,
        )
    except:
        sub_album = Sub_error(message=msg)

    return sub_album


def masterlist_dict(msgs, masterlist=None):
    # Input a list of Discord messages (NOT STRINGS).
    # Returns a dictionary in the form {str(int): submission}
    # consisting of all submissions for the chosen masterlist.
    subs_dict = {}
    entry = 1
    for msg in msgs:
        sub_album = submission_make(msg)
        if masterlist == None:
            subs_dict[str(entry)] = sub_album
            entry = entry + 1
        elif masterlist == "error" and type(sub_album).__name__ == "Sub_error":
            subs_dict[str(entry)] = sub_album
            entry = entry + 1
        elif (
            type(sub_album).__name__ != "Sub_error"
            and sub_album.masterlist == masterlist
        ):
            subs_dict[str(entry)] = sub_album
            entry = entry + 1

    return subs_dict


def discussed_check(sub_album, discussed_albums):
    # Check if a submission has been reviewed before in the server.
    try:
        row = discussed_albums.index((sub_album.title, sub_album.artist))
        return True, albums_wks.acell("C" + str(row + 2)).value
    except:
        return False, 0


async def subs_check_msg(ctx, bot, masterlist):
    # Check if there are new submissions, and if so create the mod approval message.
    # Return also the submissions dictionary.

    msgs = []

    # Fetch submission history and keep those with no reaction.
    async for msg in bot.get_channel(submissions_channel).history(limit=100):
        if not msg.reactions:
            msgs.append(msg)

    # Create the appropriate submissions dictionary.
    subs_dict = masterlist_dict(msgs, masterlist)

    # Various checks.
    discussed_artists = albums_wks.col_values(2)[1:]
    discussed_albums = list(zip(albums_wks.col_values(1)[1:], discussed_artists))
    if subs_dict:
        check_list = []
        for ind, sub in list(subs_dict.items()):
            # Check for errors.
            if type(sub).__name__ == "Sub_error":
                check_list.append(
                    "**"
                    + ind
                    + ".** "
                    + "Something went wrong with submission <"
                    + sub.message.jump_url
                    + ">."
                )
            else:
                # Check whether the album has been discussed before.
                check, week = discussed_check(sub, discussed_albums)
                if check:
                    check_list.append(
                        "**"
                        + ind
                        + ".** "
                        + sub.title
                        + " by "
                        + sub.artist
                        + " seems to have been discussed already on week "
                        + week
                        + " (submitted by "
                        + sub.submitter_name
                        + " ("
                        + str(sub.submitter_id)
                        + "), link to submission: <"
                        + sub.message.jump_url
                        + ">)."
                    )
                else:
                    check_list.append("**" + ind + ".** " + sub.sub_check_msg_full())

        # Create post.
        subs_check_msg_full = "\n".join(check_list)
        subs_check = post_split(subs_check_msg_full, 2000)
        for sub_check in subs_check:
            await ctx.send(sub_check)

        return subs_dict

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

        return []


# Add cog to bot
def setup(bot):
    bot.add_cog(Album_Submissions(bot))
