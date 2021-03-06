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
from random import shuffle, choice

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
ALBUMS_WKS = gsa.open_by_url(getenv("ALBUMS_SHEET_URL")).sheet1
WEEKS_WKS = gsa.open_by_url(getenv("ALBUMS_SHEET_URL")).get_worksheet(1)
SUBS_SHEET = gsa.open_by_url(getenv("SUBS_SHEET_URL"))

SUB_APPROVAL_CHANNEL = int(getenv("QOTD_APPROVAL_CHANNEL"))

SUBMISSIONS_CHANNEL = int(getenv("SUBMISSIONS_CHANNEL"))
VOTED_CHANNEL = int(getenv("VOTED_CHANNEL"))
NEW_CHANNEL = int(getenv("NEW_CHANNEL"))
MODERN_CHANNEL = int(getenv("MODERN_CHANNEL"))
CLASSIC_CHANNEL = int(getenv("CLASSIC_CHANNEL"))
THEME_CHANNEL = int(getenv("THEME_CHANNEL"))

MASTERLIST_CHANNEL_DICT = {
    "voted": VOTED_CHANNEL,
    "new": NEW_CHANNEL,
    "modern": MODERN_CHANNEL,
    "classic": CLASSIC_CHANNEL,
    "theme": THEME_CHANNEL,
}


class Album_Submissions(
    commands.Cog,
    name="Album Submissions",
    description="Functions to handle album submissions for the masterlists.",
):
    def __init__(self, bot):
        self.bot = bot
        self.sheet_updating = False
        self.masterlist_updating = False
        self.subs_sheet_update.start()

    @tasks.loop(hours=12)
    async def subs_sheet_update(self):
        self.sheet_updating = True
        for masterlist in MASTERLIST_CHANNEL_DICT:
            await update_subs_sheet(
                self.bot, self.bot.get_channel(SUB_APPROVAL_CHANNEL), masterlist
            )
        self.sheet_updating = False

    async def updating_check(self, ctx):
        if self.sheet_updating:
            await ctx.send("Submission sheets are currently updating. Try again later.")
            return True

        if self.masterlist_updating:
            await ctx.send(
                "Masterlist channels are currently updating. Try again later."
            )
            return True

        return False

    @commands.command(
        brief="Search for your submissions.",
        description="Search for your submissions. Optional argument: masterlist name.",
    )
    async def search_subs(self, ctx, masterlist=None):
        if await self.updating_check(ctx):
            return

        async def retrieve_sub(ctx, masterlist):
            wks = SUBS_SHEET.worksheet(masterlist.upper())
            sub_cell = wks.find(f"{ctx.author.id}")
            if sub_cell is None:
                return f"{masterlist}: No submission."
            sub_data = wks.row_values(sub_cell.row)
            return f"{masterlist}: {sub_data[0]} by {sub_data[1]} ({sub_data[2]}) ({sub_data[3]})"

        if masterlist == None:
            await ctx.send(
                f"<@!{ctx.author.id}> submissions:\n\n"
                + "\n".join(
                    [
                        await retrieve_sub(ctx, masterlist.upper())
                        for masterlist in MASTERLIST_CHANNEL_DICT
                    ]
                )
            )
        elif masterlist.lower() in MASTERLIST_CHANNEL_DICT:
            await ctx.send(
                f"<@!{ctx.author.id}> submission for {await retrieve_sub(ctx, masterlist.upper())}"
            )
        else:
            ctx.send(
                "Please provide a valid masterlist name, or no name if you wish"
                "to see all your submissions."
            )

    @commands.command(
        brief="Manually add a submission to a masterlist (for staff use only).",
        description="Manually add a submission to a masterlist (for staff use only). Use "
        "the usual submission format (i.e. Title // Artist // Year // Genre // Masterlist).",
    )
    async def submit(self, ctx):
        if await self.updating_check(ctx):
            return

        await ctx.send(
            "You ave 5 minutes to respond with your submission, "
            "or with 'stop' to stop the submission process."
        )

        def check(resp):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", timeout=300, check=check)

            if response.content.lower() == "stop":
                await ctx.send("The submission process has stopped.")
                return

            sub = submission_make(response)
            if type(sub).__name__ == "Sub_error":
                await ctx.send(
                    "There is something wrong with the format of your submission."
                )
                return

            existing_subs_dict, submitters_dict, discussed_albums = get_check_data(
                sub.masterlist
            )
            error_id = submission_check(
                sub, existing_subs_dict, submitters_dict, discussed_albums
            )

            if sub.warning == "discussed":
                await ctx.send(
                    f"**WARNING:** This album seems to have been discussed already on week {error_id}."
                )
            elif sub.warning == "duplicate":
                channel = self.bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
                sub_msg = await channel.fetch_message(error_id)
                await ctx.send(
                    f"**WARNING:** This album seems to be in {sub.masterlist.upper()} already. "
                    f"Link to existing submission: <{sub_msg.jump_url}>."
                )
            elif sub.warning == "user already in masterlist":
                channel = self.bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
                sub_msg = await channel.fetch_message(error_id)
                await ctx.send(
                    f"**WARNING:** You seem to have a submission in {sub.masterlist.upper()} already. "
                    f"Link to existing submission: <{sub_msg.jump_url}>."
                )
            else:
                await submit_album(self.bot, sub)
        except TimeoutError:
            await ctx.send("Time has run out.")
        except:
            await ctx.send("Something went wrong. Please try again.")

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
        if await self.updating_check(ctx):
            return

        # Check if an appropriate masterlist is chosen, otherwise prompt for one.
        if masterlist is None:
            subs_dict = await subs_check_msg(self.bot, ctx, masterlist=None)
        elif masterlist.lower() in (
            "voted",
            "new",
            "modern",
            "classic",
            "theme",
            "error",
            "halted",
        ):
            subs_dict = await subs_check_msg(self.bot, ctx, masterlist.lower())
        else:
            await ctx.send(
                "Please provide a valid masterlist, or 'error' if you want to fetch all "
                "new submissions with errors, or no masterlist if you want to fetch all "
                "new submissions from all lists (including those with errors)."
            )

            return

        if not subs_dict:
            return

        if masterlist == "halted":
            await ctx.send(
                "You have 30 minutes to respond with one of:\n"
                "?? 'ok' in order to approve all submissions without errors or warnings;\n"
                "?? 'reject' followed by the numbers of the submissions you want to reject "
                "(separated by ',');\n"
                "?? 'unhalt' followed by the numbers of the submissions you want to unhalt "
                "(separated by ',');\n"
                "?? 'stop' in order to stop the process."
            )

        else:
            await ctx.send(
                "You have 30 minutes to respond with one of:\n"
                "?? 'ok' in order to approve all submissions without errors or warnings;\n"
                "?? 'reject' followed by the numbers of the submissions you want to reject "
                "(separated by ',');\n"
                "?? 'halt' followed by the numbers of the submissions you want to halt "
                "for later consideration (separated by ',');\n"
                "?? 'stop' in order to stop the process."
            )

        # Submission checking options

        def check(resp):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", timeout=1800, check=check)

            if response.content.lower().startswith("stop"):
                await ctx.send("The submissions approval process has stopped.")
                return

            # Approve submissions
            elif response.content.lower().startswith("ok"):
                if masterlist == "error":
                    await ctx.send(
                        "I can't add submissions with errors to the masterlist."
                    )
                elif masterlist == "halted":
                    for _, sub in list(subs_dict.items()):
                        if type(sub).__name__ != "Sub_error" and sub.warning is None:
                            await sub.message.clear_reaction("????")
                            await submit_album(self.bot, sub)
                    await ctx.send(
                        "All new submissions without errors or warnings were added to the masterlists."
                    )
                elif masterlist is None:
                    for _, sub in list(subs_dict.items()):
                        if type(sub).__name__ != "Sub_error" and sub.warning is None:
                            await submit_album(self.bot, sub)
                    await ctx.send(
                        "All new submissions without errors or warnings were added to the masterlists."
                    )
                else:
                    for _, sub in list(subs_dict.items()):
                        if (
                            type(sub).__name__ != "Sub_error"
                            and sub.warning is None
                            and sub.masterlist == masterlist
                        ):
                            await submit_album(self.bot, sub)
                    await ctx.send(
                        "All new submissions without errors or warnings were added to the "
                        f"{masterlist.upper()} masterlist."
                    )

            # Reject submissions
            elif response.content.lower().startswith("reject"):
                rej_sub_indices, rej_sub_msgs = msgs_by_index(response, subs_dict)
                for msg in rej_sub_msgs:
                    await msg.add_reaction("???")
                if len(rej_sub_indices) == 1:
                    await ctx.send(f"Album {rej_sub_indices[0]} was rejected.")
                elif len(rej_sub_indices) > 1:
                    await ctx.send(
                        "Albums " + ", ".join(rej_sub_indices) + " were rejected."
                    )

            # Halt submissions for later consideration.
            elif response.content.lower().startswith("halt") and masterlist != "halted":
                halt_sub_indices, halt_sub_msgs = msgs_by_index(response, subs_dict)
                for msg in halt_sub_msgs:
                    await msg.add_reaction("????")
                if len(halt_sub_indices) == 1:
                    await ctx.send(f"Album {halt_sub_indices[0]} was halted.")
                elif len(halt_sub_indices) > 1:
                    await ctx.send(
                        "Albums " + ", ".join(halt_sub_indices) + " were halted."
                    )

            # Unhalt halted submissions.
            elif (
                response.content.lower().startswith("unhalt") and masterlist == "halted"
            ):
                unhalt_sub_indices, unhalt_sub_msgs = msgs_by_index(response, subs_dict)
                for msg in unhalt_sub_msgs:
                    await msg.clear_reaction("????")
                if len(unhalt_sub_indices) == 1:
                    await ctx.send(f"Album {unhalt_sub_indices[0]} was unhalted.")
                elif len(unhalt_sub_indices) > 1:
                    await ctx.send(
                        "Albums " + ", ".join(unhalt_sub_indices) + " were unhalted."
                    )

            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    "Please start the submissions approval process again."
                )

        except TimeoutError:
            await ctx.send("Time has run out.")
        except:
            await ctx.send("Something went wrong. Please try again.")

    @commands.command(
        brief="Choose a random album from a masterlist.",
        description="Choose a random album from a masterlist. Optional argument: "
        "masterlist name (i.e. one of 'voted', 'new', 'modern', 'classic', 'theme'). "
        "If no masterlist is specified, the bot will get a random album from every "
        "masterlist except 'voted'.",
    )
    async def get_random(self, ctx, masterlist=None):
        if await self.updating_check(ctx):
            return

        if masterlist is None:
            for masterlist in list(MASTERLIST_CHANNEL_DICT)[1:]:
                await random_album(ctx, masterlist)
        elif masterlist.lower() in MASTERLIST_CHANNEL_DICT:
            await random_album(ctx, masterlist)
        else:
            ctx.send(
                "Please provide a valid masterlist name, or no name if you wish"
                "to get a random album from every masterlist (except 'voted')."
            )

    @commands.command(
        brief="Pass all submissions from a masterlist to its corresponding google sheet.",
        description="Pass all submissions from a masterlist to its corresponding google sheet. "
        "Optional argument: masterlist name (i.e. one of 'voted', 'new', 'modern', 'classic', 'theme'). "
        "If no masterlist is specified, the bot will update all sheets.",
    )
    async def update_sheet(self, ctx, masterlist=None):
        if await self.updating_check(ctx):
            return

        self.sheet_updating = True

        if masterlist is None:
            for masterlist in MASTERLIST_CHANNEL_DICT:
                await update_subs_sheet(self.bot, ctx, masterlist)
        elif masterlist.lower() in MASTERLIST_CHANNEL_DICT:
            await update_subs_sheet(self.bot, ctx, masterlist.lower())
        else:
            ctx.send(
                "Please provide a valid masterlist name, or no name if you wish to update "
                "all masterlists from the sheet data."
            )

        self.sheet_updating = False

    @commands.command(
        brief="Pass all submissions from a sheet to its corresponding masterlist in a random order.",
        description="Pass all submissions from a sheet to its corresponding masterlist in a random order. "
        "Optional argument: masterlist name (i.e. one of 'voted', 'new', 'modern', 'classic', 'theme'). "
        "If no masterlist is specified, the bot will update all masterlists.",
    )
    async def update_masterlist(self, ctx, masterlist=None):
        if await self.updating_check(ctx):
            return

        self.masterlist_updating = True

        if masterlist is None:
            for masterlist in MASTERLIST_CHANNEL_DICT:
                await sheet_to_masterlist(self.bot, ctx, masterlist)
                await update_subs_sheet(self.bot, ctx, masterlist)
        elif masterlist.lower() in MASTERLIST_CHANNEL_DICT:
            await sheet_to_masterlist(self.bot, ctx, masterlist.lower())
            await update_subs_sheet(self.bot, ctx, masterlist.lower())
        else:
            ctx.send(
                "Please provide a valid masterlist name, or no name if you wish to update "
                "all masterlists from the sheet data."
            )

        self.masterlist_updating = False


def msgs_by_index(response, subs_dict):
    resp_content = response.content.split(",")
    sub_indices = []
    for thing in resp_content:
        ind = ""
        for char in thing:
            if char.isnumeric():
                ind = ind + char

        sub_indices.append(ind)

    return sub_indices, [subs_dict[ind].message for ind in sub_indices]


async def random_album(ctx, masterlist):
    album = choice(SUBS_SHEET.worksheet(masterlist.upper()).get_all_values()[1:])
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

    await ctx.send(f"{masterlist.upper()} choice: {sub.masterlist_format()}")


async def submit_album(bot, sub: Submission):
    # Submit an album.

    # If the submitter asks for a replacement:
    if sub.request == "replace":
        wks = SUBS_SHEET.worksheet(sub.masterlist.upper())
        # Locate the submitter in the spreadsheet.
        prev_sub_cell = wks.find(f"{sub.submitter_id}")
        if prev_sub_cell is not None:
            # If the submitter is in the spreadsheet, locate the message id of
            # their previous submission in the same row as their user id.
            prev_sub_row = prev_sub_cell.row
            prev_sub_msg_id = wks.acell(f"G{prev_sub_row}").value
            # Get the channel corresponding to the requested masterlist and delete
            # their previous submission.
            channel = bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
            prev_sub_msg = await channel.fetch_message(prev_sub_msg_id)
            await prev_sub_msg.delete()
            # Delete their submission from the spreadsheet.
            wks.delete_rows(prev_sub_row)

    # Submit the album in the requested masterlist.
    sub_msg = await bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist]).send(
        sub.masterlist_format()
    )
    # Add the submission to the spreadsheet.
    SUBS_SHEET.worksheet(sub.masterlist.upper()).append_row(
        [
            sub.title,
            sub.artist,
            ", ".join(sub.genres),
            sub.release_date,
            sub.submitter_name,
            f"{sub.submitter_id}",
            f"{sub_msg.id}",
        ]
    )
    # Mark the submission as accepted.
    await sub.message.add_reaction("????")


# ----------------------------------------------------------FETCHING-DATA--------------------------------------------------------


def get_existing_subs_and_submitters(masterlist):
    # Get a list of all submitters and all submissions in a masterlist.
    subs = SUBS_SHEET.worksheet(masterlist.upper()).get_all_values()[1:]
    existing_subs_in_masterlist = [(sub[0], sub[1]) for sub in subs]
    submitters_in_masterlist = [int(sub[5]) for sub in subs]

    return existing_subs_in_masterlist, submitters_in_masterlist


def get_check_data(masterlist):
    # Get all the data required for the various checks in a masterlist
    # (submitters, submissions, previously discussed albums).
    existing_subs_dict = {}
    submitters_dict = {}
    if masterlist is None or masterlist == "halted":
        for list_name in MASTERLIST_CHANNEL_DICT:
            (
                existing_subs_dict[list_name],
                submitters_dict[list_name],
            ) = get_existing_subs_and_submitters(list_name)
    elif masterlist in MASTERLIST_CHANNEL_DICT:
        (
            existing_subs_dict[masterlist],
            submitters_dict[masterlist],
        ) = get_existing_subs_and_submitters(masterlist)

    discussed_albums = [
        (entry[0], entry[1]) for entry in ALBUMS_WKS.get_all_values()[1:]
    ]

    return existing_subs_dict, submitters_dict, discussed_albums


# --------------------------------------------------------FETCHING-DATA-END-----------------------------------------------------


# -----------------------------------------------------VARIOUS-CHECK-FUNCTIONS-----------------------------------------------------


def discussed_check(sub: Submission, discussed_albums):
    # Check if a submission has been reviewed before in the server.
    try:
        row = discussed_albums.index((sub.title, sub.artist))
        return True, ALBUMS_WKS.acell(f"C{row + 2}").value
    except:
        return False, 0


def duplicate_check(sub: Submission, existing_subs_dict):
    # Check if an album is already in the masterlist.
    try:
        row = existing_subs_dict[sub.masterlist].index((sub.artist, sub.title))
        return (
            True,
            int(
                SUBS_SHEET.worksheet(sub.masterlist.upper()).acell(f"G{row + 2}").value
            ),
        )
    except:
        return False, 0


def user_already_in_masterlist_check(sub: Submission, submitters_dict):
    # Check if a user has already submitted an album in the masterlist.
    try:
        row = submitters_dict[sub.masterlist].index(sub.submitter_id)
        return (
            True,
            int(
                SUBS_SHEET.worksheet(sub.masterlist.upper()).acell(f"G{row + 2}").value
            ),
        )
    except:
        return False, 0


def submission_check(sub, existing_subs_dict, submitters_dict, discussed_albums):
    # Check whether the album has been discussed before.
    check_1, week = discussed_check(sub, discussed_albums)
    if check_1:
        sub.warning = "discussed"
        return week

    # Check whether the album is already in the masterlist.
    check_2, sub_msg_id = duplicate_check(sub, existing_subs_dict)
    if check_2:
        sub.warning = "duplicate"
        return sub_msg_id

    # Check whether the user has already submitted in the masterlist.
    check_3, sub_msg_id = user_already_in_masterlist_check(sub, submitters_dict)
    if check_3 and sub.request != "replace":
        sub.warning = "user already in masterlist"
        return sub_msg_id

    return 0


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


def masterlist_dict(msgs, masterlist):
    # Input a list of Discord messages (NOT STRINGS).
    # Returns a dictionary in the form {str(int): submission}
    # consisting of all submissions for the chosen masterlist.
    subs_dict = {}
    entry = 1
    for msg in msgs:
        sub_album = submission_make(msg)
        if masterlist is None or masterlist == "halted":
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


async def subs_check_msg(bot, ctx, masterlist):
    # Check if there are new submissions, and if so create the mod approval message.
    # Return also the submissions dictionary.

    # Fetch submission history and keep those with no reaction.
    msgs = []
    if masterlist == "halted":
        async for msg in bot.get_channel(SUBMISSIONS_CHANNEL).history(limit=100):
            if "????" in [reaction.emoji for reaction in msg.reactions]:
                msgs.append(msg)
    else:
        async for msg in bot.get_channel(SUBMISSIONS_CHANNEL).history(limit=100):
            if not msg.reactions:
                msgs.append(msg)

    # Create the appropriate submissions dictionary.
    subs_dict = masterlist_dict(msgs, masterlist)

    # Check if there are any new submissions.
    if not subs_dict:
        if masterlist is None:
            await ctx.send("There are no new submissions.")
        elif masterlist == "error":
            await ctx.send("There are no new submissions with errors.")
        elif masterlist == "halted":
            await ctx.send("There are no halted submissions.")
        else:
            await ctx.send(
                f"There are no new submissions for the {masterlist.upper()} masterlist."
            )

        return []

    # Fetch the relevant data from the submissions spreadsheet and the discussed albums.
    existing_subs_dict, submitters_dict, discussed_albums = get_check_data(masterlist)

    # Perform the various checks on new submissions.
    check_list = []
    for ind, sub in list(subs_dict.items()):
        # Check for errors.
        if type(sub).__name__ == "Sub_error":
            check_list.append(
                f"**{ind}.** Something went wrong with submission <{sub.message.jump_url}>."
            )
            continue

        # Check whether the album has been reviewed before, whether it is already in the
        # specified masterlist, or whether the user has a submission already in the
        # specified masterlist.
        error_id = submission_check(
            sub, existing_subs_dict, submitters_dict, discussed_albums
        )

        # Append the relevant warning to the submissions check message.
        check_msg = f"**{ind}.** {sub.sub_check_msg_full()}"
        if sub.warning == "discussed":
            check_msg += (
                "\n"
                f"**WARNING:** This album seems to have been discussed already on week {error_id}."
            )
        elif sub.warning == "duplicate":
            channel = bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
            sub_msg = await channel.fetch_message(error_id)
            check_msg += (
                "\n"
                f"**WARNING:** This album seems to be in {sub.masterlist.upper()} already. "
                f"Link to existing submission: <{sub_msg.jump_url}>."
            )
        elif sub.warning == "user already in masterlist":
            channel = bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
            sub_msg = await channel.fetch_message(error_id)
            check_msg += (
                "\n"
                f"**WARNING:** {sub.submitter_name} ({sub.submitter_id}) "
                f"seems to have a submission in {sub.masterlist.upper()} already. "
                f"Link to existing submission: <{sub_msg.jump_url}>."
            )

        check_list.append(check_msg)

    # Create post.
    subs_check_msg_full = "\n\n".join(check_list)
    subs_check = post_split(subs_check_msg_full, 2000)
    for sub_check in subs_check:
        await ctx.send(sub_check)

    return subs_dict


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


async def update_subs_sheet(bot, ctx, masterlist):
    # Pass all submissions from a masterlist to its corresponding sheet.
    await ctx.send(f"Updating {masterlist.upper()} sheet.")
    subs_wks = SUBS_SHEET.worksheet(masterlist.upper())
    subs_wks.clear()
    problem_subs = []
    subs_wks.append_row(
        [
            "Title",
            "Artist",
            "Year",
            "Genre",
            "Submitter Name",
            "Submitter ID",
            "Message ID",
        ]
    )
    async for msg in bot.get_channel(MASTERLIST_CHANNEL_DICT[masterlist]).history():
        try:
            sub = await masterlist_sub_make(bot, msg.content, masterlist)
            subs_wks.append_row(
                [
                    sub.title,
                    sub.artist,
                    sub.release_date,
                    ", ".join(sub.genres),
                    sub.submitter_name,
                    f"{sub.submitter_id}",
                    f"{msg.id}",
                ]
            )
            sleep(1)
        except:
            problem_subs.append(msg.jump_url)

    print(
        f"{masterlist.upper()} sheet updated ("
        + pendulum.now("America/Toronto").strftime("%Y-%m-%d, %H:%M:%S EST")
        + ")."
    )
    await ctx.send(f"{masterlist.upper()} sheet updated.")

    if problem_subs:
        await ctx.send(f"Problem subs in {masterlist.upper()}:")
        await ctx.send("\n".join(problem_subs))


# ------------------------------------------------MASTERLIST-DATA-TO-SHEET-END-------------------------------------------------


# --------------------------------------------------SHEET-DATA-TO-MASTERLIST-------------------------------------------------


async def sheet_to_masterlist(bot, ctx, masterlist):
    # Pass all submissions from a sheet to its corresponding masterlist.
    await ctx.send(f"Updating {masterlist.upper()} masterlist.")
    channel = bot.get_channel(MASTERLIST_CHANNEL_DICT[masterlist])
    await channel.purge(limit=100)
    subs_wks = SUBS_SHEET.worksheet(masterlist.upper())
    albums = subs_wks.get_all_values()[1:]
    shuffle(albums)
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

        await channel.send(sub.masterlist_format())

    await ctx.send(
        f"{masterlist.upper()} masterlist has been updated in a random order."
    )


# ------------------------------------------------SHEET-DATA-TO-MASTERLIST-END-------------------------------------------------

# Add cog to bot
def setup(bot):
    bot.add_cog(Album_Submissions(bot))
