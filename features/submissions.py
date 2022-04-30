# Library for Discord
from discord.ext import commands, tasks

# Google spreadsheets
import gspread

# Import submission class
from classes.submission_class import Submission, Sub_error

# Import post_split
from features.releases import post_split

# Library to load tokens
from os import getenv

# Libraries for various functions
from asyncio.exceptions import TimeoutError
import pendulum
from time import sleep

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
subs_sheet = gsa.open_by_url(getenv("SUBS_SHEET_URL"))

approval_channel = int(getenv("QOTD_APPROVAL_CHANNEL"))

submissions_channel = int(getenv("SUBMISSIONS_CHANNEL"))
voted_channel = int(getenv("VOTED_CHANNEL"))
new_channel = int(getenv("NEW_CHANNEL"))
modern_channel = int(getenv("MODERN_CHANNEL"))
classic_channel = int(getenv("CLASSIC_CHANNEL"))
theme_channel = int(getenv("THEME_CHANNEL"))

masterlist_channel_dict = {
    "voted": voted_channel,
    "new": new_channel,
    "modern": modern_channel,
    "classic": classic_channel,
    "theme": theme_channel,
}

# Fetch all data from the submissions spreadsheets.
existing_subs_dict = {}
submitters_dict = {}
for masterlist in masterlist_channel_dict:
    subs = subs_sheet.worksheet(masterlist.upper()).get_all_values()[1:]
    existing_subs_dict[masterlist] = [(sub[0], sub[1]) for sub in subs]
    submitters_dict[masterlist] = [int(sub[5]) for sub in subs]

discussed_artists = albums_wks.col_values(2)[1:]
discussed_albums = list(zip(albums_wks.col_values(1)[1:], discussed_artists))


class Album_Submissions(
    commands.Cog,
    name="Album Submissions",
    description="Functions to handle album submissions for the masterlists.",
):
    def __init__(self, bot):
        self.bot = bot
        self.subs_sheet_update.start()

    @tasks.loop(hours=12)
    async def subs_sheet_update(self):
        for masterlist in masterlist_channel_dict:
            await update_subs_sheet(self.bot, masterlist)

    @commands.command()
    async def sheet_update(self, ctx, masterlist=None):
        if masterlist is None:
            for masterlist in masterlist_channel_dict:
                await update_subs_sheet(self.bot, masterlist)
        else:
            await update_subs_sheet(self.bot, masterlist)

    @commands.command(
        brief="Manually add a submission to a masterlist (for staff use only)",
        description="Manually add a submission to a masterlist (for staff use only)",
    )
    async def submit(self, ctx):
        await ctx.send("You have 5 minutes to respond with your submission.")

        def check(resp):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", timeout=300.0, check=check)
            sub = submission_make(response)
            await submit_album(self.bot, sub)
        except TimeoutError:
            await ctx.send("Time has run out.")
        except:
            await ctx.send("Something went wrong. Please try again.")

    @commands.command(
        brief="Pass all submissions from a sheet to its corresponding masterlist.",
        description="Pass all submissions from a sheet to its corresponding masterlist. "
        "Optional argument: masterlist name masterlist name (i.e. one of 'voted', 'new', 'modern', "
        "'classic', 'theme'). If no masterlist is specified, the bot will update all masterlists.",
    )
    async def update_masterlist(self, ctx, masterlist=None):
        if masterlist is None:
            for masterlist in masterlist_channel_dict:
                await sheet_to_masterlist(self.bot, masterlist)
                await ctx.send(
                    f"{masterlist.upper()} masterlist has been updated from the sheet data."
                )
        elif masterlist.lower() in masterlist_channel_dict:
            await sheet_to_masterlist(self.bot, masterlist.lower())
            await ctx.send(
                f"{masterlist.upper()} masterlist has been updated from the sheet data."
            )
        else:
            ctx.send(
                "Please provide a valid masterlist name, or no name if you wish to update "
                "all masterlists from the sheet data."
            )

    @commands.command(
        brief="Fetch and approve or reject submissions for the masterlists.",
        description="Fetch and approve or reject submissions for the masterlists. "
        "Optional argument: masterlist name (i.e. one of 'voted', 'new', 'modern', "
        "'classic', 'theme') to only fetch submissions for that masterlist, or 'error' to fetch "
        "messages in #submissions which cannot be correctly interpreted as a submission by the bot. "
        "Once the submissions have been fetched, you have 20 minutes to respond with 'ok' in order "
        "to approve all submissions, 'reject' followed by the numbers of the submissions you want to "
        "reject, or 'stop' to stop the process.",
    )
    async def subs(self, ctx, masterlist=None):
        # Check if an appropriate masterlist is chosen, otherwise prompt for one.
        if masterlist is None or masterlist.lower() in (
            "voted",
            "new",
            "modern",
            "classic",
            "theme",
            "error",
        ):
            subs_dict = await subs_check_msg(ctx, self.bot, masterlist.lower())
            if not subs_dict:
                return

            await ctx.send(
                "You have 30 minutes to respond with 'ok' in order to approve all "
                "submissions, 'reject' followed by the numbers of the submissions "
                "you want to reject, or 'stop' to stop the process."
            )

            # Submission checking options

            def check(resp):
                return resp.author == ctx.author and resp.channel == ctx.channel

            try:
                response = await self.bot.wait_for(
                    "message", timeout=1800.0, check=check
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
                    elif masterlist is None:
                        for _, sub in list(subs_dict.items()):
                            if type(sub).__name__ != "Sub_error":
                                await submit_album(self.bot, sub)
                        await ctx.send(
                            "All new submissions without errors were added to the masterlists."
                        )

                    else:
                        for _, sub in list(subs_dict.items()):
                            if (
                                type(sub).__name__ != "Sub_error"
                                and sub.masterlist == masterlist
                            ):
                                await submit_album(self.bot, sub)
                        await ctx.send(
                            "All new submissions without errors were added to the "
                            f"{masterlist.upper()} masterlist."
                        )

                # Reject and delete submissions
                elif response.content.lower().startswith("reject"):
                    resp_content = response.content.split(",")
                    sub_indices = []
                    for ind in resp_content:
                        if ind[0] == " ":
                            ind = ind[1:]
                        try:
                            int(ind)
                            sub_indices.append(ind)
                        except:
                            pass
                    sub_msgs = [subs_dict[ind].message for ind in sub_indices]
                    if len(sub_indices) == 1:
                        await ctx.send(
                            "Are you sure you want to reject album "
                            f"{sub_indices[0]} (y/n)?"
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
                            await ctx.send(f"Album {sub_indices[0]} was rejected.")
                        elif len(sub_indices) > 1:
                            await ctx.send(
                                "Albums " + ", ".join(sub_indices) + " were rejected."
                            )
                    else:
                        if len(sub_indices) == 1:
                            await ctx.send(f"Album {sub_indices[0]} was not rejected.")
                        elif len(sub_indices) > 1:
                            await ctx.send(
                                "Albums "
                                + ", ".join(sub_indices)
                                + " were not rejected."
                            )
                else:
                    await ctx.send(
                        f"I don't know what you mean by '{response.content}'. "
                        "Please start the submissions approval process again."
                    )
                return

            except TimeoutError:
                await ctx.send("Time has run out.")
            except:
                await ctx.send("Something went wrong. Please try again.")

        else:
            await ctx.send(
                "Please provide a valid masterlist, or 'error' if you want to fetch all "
                "new submissions with errors, or no masterlist if you want to fetch all "
                "new submissions from all lists (including those with errors)."
            )


async def submit_album(bot, sub: Submission):
    # Submit an album.
    await bot.get_channel(masterlist_channel_dict[sub.masterlist]).send(
        sub.masterlist_format()
    )
    subs_sheet.worksheet(sub.masterlist.upper()).append_row(
        [
            sub.artist,
            sub.title,
            ", ".join(sub.genres),
            sub.release_date,
            sub.submitter_name,
            f"{sub.submitter_id}",
        ]
    )
    await sub.message.add_reaction("🆗")


# -----------------------------------------------------VARIOUS-CHECK-FUNCTIONS-----------------------------------------------------


def discussed_check(sub: Submission):
    # Check if a submission has been reviewed before in the server.
    try:
        row = discussed_albums.index((sub.title, sub.artist))
        return True, albums_wks.acell(f"C{row + 2}").value
    except:
        return False, 0


def duplicate_check(sub: Submission):
    # Check if an album is already in the masterlist.
    if (sub.artist, sub.title) in existing_subs_dict[sub.masterlist]:
        return True
    else:
        return False


def submitted_already(sub: Submission):
    # Check if a user has already submitted an album in the masterlist.
    if sub.submitter_id in submitters_dict[sub.masterlist]:
        return True
    else:
        return False


# ---------------------------------------------------VARIOUS-CHECK-FUNCTIONS-END-------------------------------------------------


# ---------------------------------------------------APPROVAL-MESSAGE-CREATION--------------------------------------------------


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
        if masterlist is None:
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
    if subs_dict:
        check_list = []
        for ind, sub in list(subs_dict.items()):
            # Check for errors.
            if type(sub).__name__ == "Sub_error":
                check_list.append(
                    f"**{ind}.** Something went wrong with submission <{sub.message.jump_url}>."
                )
            else:
                # Check whether the album has been discussed before.
                check, week = discussed_check(sub)
                if check:
                    check_list.append(
                        f"**{ind}.** {sub.title} by {sub.artist} "
                        f"seems to have been discussed already on week {week} "
                        f"(submitted by {sub.submitter_name} ({sub.submitter_id}))."
                    )
                else:
                    # Check whether the album is already in the masterlist.
                    check = duplicate_check(sub)
                    if check:
                        check_list.append(
                            f"**{ind}.** {sub.title} by {sub.artist} "
                            f"seems to be in {sub.masterlist.upper()} already "
                            f"(submitted by {sub.submitter_name} ({sub.submitter_id}))."
                        )
                    else:
                        # Check whether the user has already submitted in the masterlist.
                        check = submitted_already(sub)
                        if check and sub.request != "replace":
                            check_list.append(
                                f"**{ind}.** "
                                f"{sub.submitter_name} ({sub.submitter_id}) "
                                f"seems to have a submission in {sub.masterlist.upper()} already."
                            )
                        else:
                            check_list.append(f"**{ind}.** {sub.sub_check_msg_full()}")

        # Create post.
        subs_check_msg_full = "\n".join(check_list)
        subs_check = post_split(subs_check_msg_full, 2000)
        for sub_check in subs_check:
            await ctx.send(sub_check)

        return subs_dict

    else:
        if masterlist is None:
            await ctx.send("There are no new submissions.")
        elif masterlist == "error":
            await ctx.send("There are no new submissions with errors.")
        else:
            await ctx.send(
                f"There are no new submissions for the {masterlist.upper()} masterlist."
            )

        return []


# ------------------------------------------------APPROVAL-MESSAGE-CREATION-END-------------------------------------------------


# --------------------------------------------------MASTERLIST-DATA-TO-SHEET--------------------------------------------------


async def masterlist_sub_make(bot, post, masterlist):
    # Create a submission from a formatted submission message in a masterlist.
    # Input a string (NOT A DISCORD MESSAGE).
    post_split = post.split("_by_")
    sub_data = [post_split[0]]
    post_split = post_split[1].split("(", 1)
    sub_data.append(post_split[0])
    post_split = post_split[1].split(")", 1)
    sub_data.append(post_split[0])
    post_split = post_split[1][2:].split(")")
    sub_data.append(post_split[0])
    id = ""
    for i in post_split[1]:
        if i.isnumeric():
            id = id + i
    sub_data.append(int(id))
    user = await bot.fetch_user(int(id))
    sub_data.append(user.display_name)

    sub_album = Submission(
        artist=sub_data[1],
        title=sub_data[0],
        genres=sub_data[3],
        release_date=sub_data[2],
        submitter_name=sub_data[5],
        submitter_id=sub_data[4],
        masterlist=masterlist,
        message=None,
    )

    return sub_album


async def update_subs_sheet(bot, masterlist):
    subs_wks = subs_sheet.worksheet(masterlist.upper())
    subs_wks.clear()
    problem_subs = []
    subs_wks.append_row(
        [
            "Title",
            "Artist",
            "Genre",
            "Year",
            "Submitter Name",
            "Submitter ID",
            "Message ID",
        ]
    )
    async for msg in bot.get_channel(masterlist_channel_dict[masterlist]).history():
        try:
            sub = await masterlist_sub_make(bot, msg.content, masterlist)
            subs_wks.append_row(
                [
                    sub.title,
                    sub.artist,
                    ", ".join(sub.genres),
                    sub.release_date,
                    sub.submitter_name,
                    f"{sub.submitter_id}",
                    f"{msg.id}",
                ]
            )
            sleep(1)
        except:
            problem_subs.append(msg.jump_url)

    print(
        f"{masterlist.upper()} sheet updated. ("
        + pendulum.now("America/Toronto").strftime("%Y-%m-%d, %H:%M:%S EST")
        + ")."
    )
    if problem_subs:
        print(f"Problem subs in {masterlist.upper()}:")
        for problem_sub in problem_subs:
            print(problem_sub)


# ------------------------------------------------MASTERLIST-DATA-TO-SHEET-END-------------------------------------------------


# --------------------------------------------------SHEET-DATA-TO-MASTERLIST-------------------------------------------------


async def sheet_to_masterlist(bot, masterlist):
    # Pass all submissions from a sheet to its corresponding masterlist.
    subs_wks = subs_sheet.worksheet(masterlist.upper())
    albums = subs_wks.get_all_values()[1:]
    for album in albums:
        sub = Submission(
            artist=album[1],
            title=album[0],
            genres=album[2],
            release_date=album[3],
            submitter_name=album[4],
            submitter_id=album[5],
            masterlist=masterlist,
            message=None,
        )

        await bot.get_channel(masterlist_channel_dict[masterlist]).send(
            sub.masterlist_format()
        )


# ------------------------------------------------SHEET-DATA-TO-MASTERLIST-END-------------------------------------------------

# Add cog to bot
def setup(bot):
    bot.add_cog(Album_Submissions(bot))
