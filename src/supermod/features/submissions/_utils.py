from random import choice
from typing import Optional

from discord import Message

from supermod._utils import *
from supermod.album_classes import Sub, SubError
from supermod.features.submissions._constants import *


def msgs_by_index(
    response: Message, subs_dict: dict[str, Sub | SubError]
) -> tuple[list[str], list[Message]]:
    resp_content = response.content.split(",")
    sub_indices = []
    sub_msgs = []
    for thing in resp_content:
        ind = ""
        for char in thing:
            if char.isnumeric():
                ind += char

        sub_indices.append(ind)
        msg = subs_dict[ind].message
        assert msg is not None
        sub_msgs.append(msg)

    return sub_indices, sub_msgs


def _safe_int(value: str) -> int:
    """Parse an int, returning -1 on failure (e.g. blank or non-numeric cell)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def random_album(masterlist: str) -> Optional[Sub]:
    rows = SUBS_SHEET.worksheet(masterlist.upper()).get_all_values()[1:]
    unique: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        unique.setdefault((row[0], row[1]), row)
    if not unique:
        return None
    album = choice(list(unique.values()))
    sub = Sub(
        artist=album[1],
        title=album[0],
        genres=album[3],
        release_date=album[2],
        submitter_name=album[4],
        submitter_id=album[5],
        masterlist=masterlist,
        message=None,
    )

    return sub


def get_existing_subs_and_submitters(
    masterlist: str,
) -> tuple[list[tuple[str, str]], list[int]]:
    """Get all submitters and submissions in a masterlist."""
    subs: list[list[str]] = SUBS_SHEET.worksheet(masterlist.upper()).get_all_values()[
        1:
    ]
    existing_subs_in_masterlist = [(sub[0], sub[1]) for sub in subs]
    submitters_in_masterlist = [_safe_int(sub[5]) for sub in subs]

    return existing_subs_in_masterlist, submitters_in_masterlist


def get_check_data(
    masterlist: Optional[str],
) -> tuple[
    dict[str, list[tuple[str, str]]], dict[str, list[int]], list[tuple[str, str]]
]:
    """
    Get the data required for masterlist checks (submitters, submissions,
    previously discussed albums)."""
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


def discussed_check(
    sub: Sub, discussed_albums: list[tuple[str, str]]
) -> tuple[bool, int]:
    """Check if a submission has been reviewed before in the server."""
    try:
        row = discussed_albums.index((sub.title, sub.artist))
        cell = ALBUMS_WKS.acell(f"C{row + 2}")
        assert cell is not None
        value = cell.value
        assert value is not None
        return True, int(value)
    except (ValueError, AssertionError):
        return False, 0


def duplicate_check(
    sub: Sub, existing_subs_dict: dict[str, list[tuple[str, str]]]
) -> tuple[bool, int]:
    """Check if an album is already in the masterlist."""
    try:
        row = existing_subs_dict[sub.masterlist].index((sub.title, sub.artist))
        cell = SUBS_SHEET.worksheet(sub.masterlist.upper()).acell(f"G{row + 2}")
        assert cell is not None
        value = cell.value
        assert value is not None
        return True, int(value)
    except (ValueError, AssertionError):
        return False, 0


def user_already_in_masterlist_check(
    sub: Sub, submitters_dict: dict[str, list[int]]
) -> tuple[bool, int]:
    """Check if a user has already submitted an album in the masterlist."""
    try:
        row = submitters_dict[sub.masterlist].index(sub.submitter_id)
        cell = SUBS_SHEET.worksheet(sub.masterlist.upper()).acell(f"G{row + 2}")
        assert cell is not None
        value = cell.value
        assert value is not None
        return True, int(value)
    except (ValueError, AssertionError):
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


def submission_make(msg: Message) -> Sub | SubError:
    """Build a Sub from a Discord message, or a SubError on failure."""
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
    except Exception as e:
        print_info(f"{type(e).__name__}: {e}")
        sub_album = SubError(message=msg)

    return sub_album


def masterlist_dict(
    msgs: list[Message], masterlist: Optional[str]
) -> dict[str, Sub | SubError]:
    """
    Map Discord messages to their submissions for the chosen masterlist as
    {str(index): submission}."""
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
