from random import choice, shuffle
from time import sleep

from discord import Message
from discord.ext.commands import Bot, Context

from ...album_classes import Sub, SubError
from ...utils import *
from ..newsletter.newsletter import post_split
from .subs_constants import *


def msgs_by_index(
    response: Message, subs_dict: dict[str, Sub | SubError]
) -> tuple[list[str], list[Optional[Message]]]:
    resp_content = response.content.split(",")
    sub_indices = []
    for thing in resp_content:
        ind = ""
        for char in thing:
            if char.isnumeric():
                ind += char

        sub_indices.append(ind)

    return sub_indices, [subs_dict[ind].message for ind in sub_indices]


async def random_album(ctx: Context, masterlist: str) -> None:
    album = choice(SUBS_SHEET.worksheet(masterlist.upper()).get_all_values()[1:])
    sub = Sub(
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


async def submit_album(bot: Bot, sub: Sub):
    """
    Submit an album.
    """

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
    assert sub.message is not None
    await sub.message.add_reaction("🆗")


# ----------------------------------------------------------FETCHING-DATA--------------------------------------------------------


def get_existing_subs_and_submitters(
    masterlist: str,
) -> tuple[list[tuple[str, str]], list[int]]:
    """
    Get a list of all submitters and all submissions in a masterlist.
    """
    subs: list[list[str]] = SUBS_SHEET.worksheet(masterlist.upper()).get_all_values()[
        1:
    ]
    existing_subs_in_masterlist = [(sub[0], sub[1]) for sub in subs]
    submitters_in_masterlist = [int(sub[5]) for sub in subs]

    return existing_subs_in_masterlist, submitters_in_masterlist


def get_check_data(
    masterlist: Optional[str],
) -> tuple[
    dict[str, list[tuple[str, str]]], dict[str, list[int]], list[tuple[str, str]]
]:
    """
    Get all the data required for the various checks in a masterlist
    (submitters, submissions, previously discussed albums).
    """
    existing_subs_dict: dict[str, list[tuple[str, str]]] = {}
    submitters_dict: dict[str, list[int]] = {}
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


def discussed_check(
    sub: Sub, discussed_albums: list[tuple[str, str]]
) -> tuple[bool, int]:
    """
    Check if a submission has been reviewed before in the server.
    """
    try:
        row = discussed_albums.index((sub.title, sub.artist))
        cell = ALBUMS_WKS.acell(f"C{row + 2}")
        assert cell is not None
        value = cell.value
        assert value is not None
        return True, int(value)
    except:
        return False, 0


def duplicate_check(
    sub: Sub, existing_subs_dict: dict[str, list[tuple[str, str]]]
) -> tuple[bool, int]:
    """
    Check if an album is already in the masterlist.
    """
    try:
        row = existing_subs_dict[sub.masterlist].index((sub.artist, sub.title))
        cell = SUBS_SHEET.worksheet(sub.masterlist.upper()).acell(f"G{row + 2}")
        assert cell is not None
        value = cell.value
        assert value is not None
        return True, int(value)
    except:
        return False, 0


def user_already_in_masterlist_check(
    sub: Sub, submitters_dict: dict[str, list[int]]
) -> tuple[bool, int]:
    """
    Check if a user has already submitted an album in the masterlist.
    """
    try:
        row = submitters_dict[sub.masterlist].index(sub.submitter_id)
        cell = SUBS_SHEET.worksheet(sub.masterlist.upper()).acell(f"G{row + 2}")
        assert cell is not None
        value = cell.value
        assert value is not None
        return True, int(value)
    except:
        return False, 0


def submission_check(
    sub: Sub,
    existing_subs_dict: dict[str, list[tuple[str, str]]],
    submitters_dict: dict[str, list[int]],
    discussed_albums: list[tuple[str, str]],
) -> int:
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


def submission_make(msg: Message) -> Sub | SubError:
    """
    Input a Discord message (NOT A STRING).
    Returns a Submission class if things go right or
    a Sub_error class if things go wrong.
    """
    try:
        sub_message = msg.content
        request = "add"
        if sub_message.lower().startswith("replace"):
            request = "replace"
            sub_message = sub_message[sub_message.lower().find("with") + 4 :]
        if sub_message[0] == ":":
            sub_message = sub_message[1:]

        sub_data = sub_message.split("//")
        sub_album = Sub(
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
        sub_album = SubError(message=msg)

    return sub_album


def masterlist_dict(
    msgs: list[Message], masterlist: Optional[str]
) -> dict[str, Sub | SubError]:
    """
    Input a list of Discord messages (NOT STRINGS).
    Returns a dictionary in the form {str(int): submission}
    consisting of all submissions for the chosen masterlist.
    """
    subs_dict = {}
    entry = 1
    for msg in msgs:
        sub_album = submission_make(msg)
        if (
            masterlist is None
            or masterlist == "halted"
            or (isinstance(sub_album, Sub) and sub_album.masterlist == masterlist)
            or (isinstance(sub_album, SubError) and masterlist == "error")
        ):
            subs_dict[str(entry)] = sub_album
            entry += 1

    return subs_dict


async def subs_check_msg(
    bot: Bot, ctx: Context, masterlist: Optional[str]
) -> dict[str, Sub | SubError]:
    """
    Check if there are new submissions, and if so create the mod approval message.
    Return also the submissions dictionary.
    """
    # Fetch submission history and keep those with no reaction.
    msgs = []
    if masterlist == "halted":
        async for msg in bot.get_channel(SUBMISSIONS_CHANNEL).history(limit=100):
            if "🇭" in [reaction.emoji for reaction in msg.reactions]:
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

        return {}

    # Fetch the relevant data from the submissions spreadsheet and the discussed albums.
    existing_subs_dict, submitters_dict, discussed_albums = get_check_data(masterlist)

    # Perform the various checks on new submissions.
    check_list = []
    for ind, sub in subs_dict.items():
        # Check for errors.
        if isinstance(sub, SubError):
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


async def masterlist_sub_make(bot: Bot, post: str, masterlist: str) -> Sub:
    """
    Create a submission from a formatted submission message in a masterlist.
    Input a string (NOT A DISCORD MESSAGE).
    """
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
            id += i
    sub_data.append(id)
    user = await bot.fetch_user(int(id))
    sub_data.append(user.display_name)

    sub_album = Sub(
        artist=sub_data[1],
        title=sub_data[0],
        genres=sub_data[3],
        release_date=sub_data[2],
        submitter_name=sub_data[5],
        submitter_id=int(sub_data[4]),
        masterlist=masterlist,
        message=None,
    )

    return sub_album


async def update_subs_sheet(bot: Bot, ctx: Context, masterlist: str) -> None:
    """
    Pass all submissions from a masterlist to its corresponding sheet.
    """
    print_info(f"Updating {masterlist.upper()} sheet.")
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

    print_info(f"{masterlist.upper()} sheet updated.")
    await ctx.send(f"{masterlist.upper()} sheet updated.")

    if problem_subs:
        await ctx.send(f"Problem subs in {masterlist.upper()}:")
        await ctx.send("\n".join(problem_subs))


# ------------------------------------------------MASTERLIST-DATA-TO-SHEET-END-------------------------------------------------


# --------------------------------------------------SHEET-DATA-TO-MASTERLIST-------------------------------------------------


async def sheet_to_masterlist(bot: Bot, ctx: Context, masterlist: str) -> None:
    """
    Pass all submissions from a sheet to its corresponding masterlist.
    """
    print_info(f"Updating {masterlist.upper()} masterlist.")

    await ctx.send(f"Updating {masterlist.upper()} masterlist.")

    channel = bot.get_channel(MASTERLIST_CHANNEL_DICT[masterlist])
    await channel.purge(limit=100)
    subs_wks = SUBS_SHEET.worksheet(masterlist.upper())
    albums = subs_wks.get_all_values()[1:]
    shuffle(albums)
    for album in albums:
        sub = Sub(
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

    print_info(f"{masterlist.upper()} masterlist has been updated in a random order.")

    await ctx.send(
        f"{masterlist.upper()} masterlist has been updated in a random order."
    )


# ------------------------------------------------SHEET-DATA-TO-MASTERLIST-END-------------------------------------------------
