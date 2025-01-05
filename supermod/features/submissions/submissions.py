from asyncio.exceptions import TimeoutError  # pylint: disable=redefined-builtin
from random import shuffle
from time import sleep
from typing import Optional

from discord import Message
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Cog, Context

from ...mode_switch import LOCAL_MODE
from ...utils import *
from ..newsletter.news_utils import post_split
from .subs_constants import *
from .subs_utils import *


class Submissions(
    Cog,
    name="Album Submissions",
    description="Functions to handle album submissions for the masterlists.",
):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.sheet_updating: bool = False
        self.masterlist_updating: bool = False

        if LOCAL_MODE == "ON":
            print_info("Submission sheets will not be updated (LOCAL_MODE: ON).")
        else:
            self.subs_sheet_update.start()

    @tasks.loop(hours=12)
    async def subs_sheet_update(self):
        self.sheet_updating = True
        for masterlist in MASTERLIST_CHANNEL_DICT:
            await self._update_subs_sheet(
                self.bot.get_channel(SUB_APPROVAL_CHANNEL), masterlist  # type: ignore[reportArgumentType]
            )
        self.sheet_updating = False

    @commands.command(
        brief="Search for your submissions.",
        description="Search for your submissions. Optional argument: masterlist name.",
    )
    async def my_subs(self, ctx: Context, masterlist: Optional[str] = None):
        if await self._updating_check(ctx):
            return

        async def retrieve_sub(ctx: Context, masterlist: str):
            wks = SUBS_SHEET.worksheet(masterlist.upper())
            sub_cell = wks.find(f"{ctx.author.id}")
            if sub_cell is None:
                return f"{masterlist}: No submission."
            sub_data = wks.row_values(sub_cell.row)
            return f"{masterlist}: {sub_data[0]} by {sub_data[1]} ({sub_data[2]}) ({sub_data[3]})"

        if masterlist is None:
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
            await ctx.send(
                "Please provide a valid masterlist name, or no name if you wish"
                "to see all your submissions."
            )

    @commands.command(
        brief="Manually add a submission to a masterlist (for staff use only).",
        description="Manually add a submission to a masterlist (for staff use only). Use "
        + "the usual submission format (i.e. Title // Artist // Year // Genre // Masterlist).",
    )
    @commands.has_role(STAFF_ROLE)
    async def submit(self, ctx: Context):
        if await self._updating_check(ctx):
            return

        await ctx.send(
            "You have 5 minutes to respond with your submission, "
            + "or with 'stop' to stop the submission process."
        )

        def check(resp: Message):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", timeout=300, check=check)

            if response.content.lower() == "stop":
                await ctx.send("The submission process has stopped.")
                return

            sub = submission_make(response)
            if isinstance(sub, SubError):
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
                    + f"Link to existing submission: <{sub_msg.jump_url}>."
                )
            elif sub.warning == "user already in masterlist":
                channel = self.bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
                sub_msg = await channel.fetch_message(error_id)
                await ctx.send(
                    f"**WARNING:** You seem to have a submission in {sub.masterlist.upper()} already. "
                    + f"Link to existing submission: <{sub_msg.jump_url}>."
                )
            else:
                await self._submit_album(sub)
        except TimeoutError:
            await ctx.send("Time has run out.")
        except Exception as e:
            print_info(f"{type(e).__name__}: {e}")
            await ctx.send("Something went wrong. Please try again.")

    @commands.command(
        brief="Fetch and approve or reject submissions for the masterlists.",
        description="Fetch and approve or reject submissions for the masterlists. "
        "Optional argument: masterlist name (i.e. one of 'voted', 'new', 'modern', 'classic', 'theme', 'anything') "
        + "to only fetch submissions for that masterlist, or 'error' to fetch messages in #submissions "
        + "which cannot be correctly interpreted as a submission by the bot. "
        + "Once the submissions have been fetched, you have 20 minutes to respond with 'ok' in order "
        + "to approve all submissions, 'reject' followed by the numbers of the submissions you want to "
        + "reject, or 'stop' to stop the process.",
    )
    @commands.has_role(STAFF_ROLE)
    async def subs(self, ctx: Context, masterlist: Optional[str] = None):
        if await self._updating_check(ctx):
            return

        # Check if an appropriate masterlist is chosen, otherwise prompt for one.
        if masterlist is None:
            subs_dict = await self._subs_check_msg(ctx, masterlist=None)
        elif masterlist.lower() in list(MASTERLIST_CHANNEL_DICT.keys()) + [
            "error",
            "halted",
        ]:
            subs_dict = await self._subs_check_msg(ctx, masterlist.lower())
        else:
            await ctx.send(
                "Please provide a valid masterlist, or 'error' if you want to fetch all "
                + "new submissions with errors, or no masterlist if you want to fetch all "
                + "new submissions from all lists (including those with errors)."
            )

            return

        if not subs_dict:
            return

        if masterlist == "halted":
            await ctx.send(
                "You have 30 minutes to respond with one of:\n"
                + "· 'ok' in order to approve all submissions without errors or warnings;\n"
                + "· 'reject' followed by the numbers of the submissions you want to reject "
                + "(separated by ',');\n"
                + "· 'unhalt' followed by the numbers of the submissions you want to unhalt "
                + "(separated by ',');\n"
                + "· 'stop' in order to stop the process."
            )

        else:
            await ctx.send(
                "You have 30 minutes to respond with one of:\n"
                + "· 'ok' in order to approve all submissions without errors or warnings;\n"
                + "· 'reject' followed by the numbers of the submissions you want to reject "
                + "(separated by ',');\n"
                + "· 'halt' followed by the numbers of the submissions you want to halt "
                + "for later consideration (separated by ',');\n"
                + "· 'stop' in order to stop the process."
            )

        # Submission checking options

        def check(resp: Message):
            return resp.author == ctx.author and resp.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", timeout=1800, check=check)

            if response.content.lower().startswith("stop"):
                await ctx.send("The submissions approval process has stopped.")
                return

            # Approve submissions
            if response.content.lower().startswith("ok"):
                if masterlist == "error":
                    await ctx.send(
                        "I can't add submissions with errors to the masterlist."
                    )
                elif masterlist == "halted":
                    for _, sub in list(subs_dict.items()):
                        if isinstance(sub, Sub) and sub.warning is None:
                            assert sub.message is not None
                            await sub.message.clear_reaction("🇭")
                            await self._submit_album(sub)
                    await ctx.send(
                        "All new submissions without errors or warnings were added to the masterlists."
                    )
                elif masterlist is None:
                    for _, sub in subs_dict.items():
                        if isinstance(sub, Sub) and sub.warning is None:
                            await self._submit_album(sub)
                    await ctx.send(
                        "All new submissions without errors or warnings were added to the masterlists."
                    )
                else:
                    for _, sub in subs_dict.items():
                        if (
                            isinstance(sub, Sub)
                            and sub.warning is None
                            and sub.masterlist == masterlist
                        ):
                            await self._submit_album(sub)
                    await ctx.send(
                        "All new submissions without errors or warnings were added to the "
                        f"{masterlist.upper()} masterlist."
                    )

            # Reject submissions
            elif response.content.lower().startswith("reject"):
                rej_sub_indices, rej_sub_msgs = msgs_by_index(response, subs_dict)
                for msg in rej_sub_msgs:
                    await msg.add_reaction("❌")
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
                    await msg.add_reaction("🇭")
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
                    await msg.clear_reaction("🇭")
                if len(unhalt_sub_indices) == 1:
                    await ctx.send(f"Album {unhalt_sub_indices[0]} was unhalted.")
                elif len(unhalt_sub_indices) > 1:
                    await ctx.send(
                        "Albums " + ", ".join(unhalt_sub_indices) + " were unhalted."
                    )

            else:
                await ctx.send(
                    f"I don't know what you mean by '{response.content}'. "
                    + "Please start the submissions approval process again."
                )

        except TimeoutError:
            await ctx.send("Time has run out.")
        except Exception as e:
            print_info(f"{type(e).__name__}: {e}")
            await ctx.send("Something went wrong. Please try again.")

    @commands.command(
        brief="Choose a random album from a masterlist.",
        description="Choose a random album from a masterlist. Optional argument: "
        + "masterlist name (i.e. one of 'voted', 'new', 'modern', 'classic', 'theme', 'anything'). "
        + "If no masterlist is specified, the bot will get a random album from every "
        + "masterlist except 'voted'.",
    )
    @commands.has_role(STAFF_ROLE)
    async def get_random(self, ctx: Context, masterlist: Optional[str] = None):
        if await self._updating_check(ctx):
            return

        if masterlist is None:
            for mlist in [
                key for key in MASTERLIST_CHANNEL_DICT.keys() if key != "voted"
            ]:
                sub = random_album(mlist)
                await ctx.send(f"{mlist.upper()} choice: {sub.masterlist_format()}")
        elif masterlist.lower() in MASTERLIST_CHANNEL_DICT:
            sub = random_album(masterlist)
            await ctx.send(f"{masterlist.upper()} choice: {sub.masterlist_format()}")
        else:
            await ctx.send(
                "Please provide a valid masterlist name, or no name if you wish"
                + "to get a random album from every masterlist (except 'voted')."
            )

    @commands.command(
        brief="Pass all submissions from a masterlist to its corresponding google sheet.",
        description="Pass all submissions from a masterlist to its corresponding google sheet. "
        + "Optional argument: masterlist name (i.e. one of 'voted', 'new', 'modern', 'classic', 'theme', 'anything'). "
        + "If no masterlist is specified, the bot will update all sheets.",
    )
    @commands.has_role(STAFF_ROLE)
    async def update_sheet(self, ctx: Context, masterlist: Optional[str] = None):
        if await self._updating_check(ctx):
            return

        self.sheet_updating = True

        if masterlist is None:
            for mlist in MASTERLIST_CHANNEL_DICT:
                await self._update_subs_sheet(ctx, mlist)
        elif masterlist.lower() in MASTERLIST_CHANNEL_DICT:
            await self._update_subs_sheet(ctx, masterlist.lower())
        else:
            await ctx.send(
                "Please provide a valid masterlist name, or no name if you wish to update "
                + "all masterlists from the sheet data."
            )

        self.sheet_updating = False

    @commands.command(
        brief="Pass all submissions from a sheet to its corresponding masterlist in a random order.",
        description="Pass all submissions from a sheet to its corresponding masterlist in a random order. "
        "Optional argument: masterlist name (i.e. one of 'voted', 'new', 'modern', 'classic', 'theme', 'anything'). "
        + "If no masterlist is specified, the bot will update all masterlists.",
    )
    @commands.has_role(STAFF_ROLE)
    async def update_masterlist(self, ctx: Context, masterlist: Optional[str] = None):
        if await self._updating_check(ctx):
            return

        self.masterlist_updating = True

        if masterlist is None:
            for mlist in MASTERLIST_CHANNEL_DICT:
                await self._sheet_to_masterlist(ctx, mlist)
                await self._update_subs_sheet(ctx, mlist)
        elif masterlist.lower() in MASTERLIST_CHANNEL_DICT:
            await self._sheet_to_masterlist(ctx, masterlist.lower())
            await self._update_subs_sheet(ctx, masterlist.lower())
        else:
            await ctx.send(
                "Please provide a valid masterlist name, or no name if you wish to update "
                + "all masterlists from the sheet data."
            )

        self.masterlist_updating = False

    async def _updating_check(self, ctx: Context):
        if self.sheet_updating:
            await ctx.send("Submission sheets are currently updating. Try again later.")
            return True

        if self.masterlist_updating:
            await ctx.send(
                "Masterlist channels are currently updating. Try again later."
            )
            return True

        return False

    async def _submit_album(self, sub: Sub):
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
                assert prev_sub_msg_id is not None
                prev_sub_msg_id = int(prev_sub_msg_id)
                # Get the channel corresponding to the requested masterlist and delete
                # their previous submission.
                channel = self.bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
                prev_sub_msg = await channel.fetch_message(prev_sub_msg_id)
                await prev_sub_msg.delete()
                # Delete their submission from the spreadsheet.
                wks.delete_rows(prev_sub_row)

        # Submit the album in the requested masterlist.
        sub_msg = await self.bot.get_channel(
            MASTERLIST_CHANNEL_DICT[sub.masterlist]
        ).send(sub.masterlist_format())
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

    async def _subs_check_msg(
        self, ctx: Context, masterlist: Optional[str]
    ) -> dict[str, Sub | SubError]:
        """
        Check if there are new submissions, and if so create the mod approval message.
        Return also the submissions dictionary.
        """
        # Fetch submission history and keep those with no reaction.
        msgs = []
        if masterlist == "halted":
            async for msg in self.bot.get_channel(SUBMISSIONS_CHANNEL).history(
                limit=100
            ):
                if "🇭" in [reaction.emoji for reaction in msg.reactions]:
                    msgs.append(msg)
        else:
            async for msg in self.bot.get_channel(SUBMISSIONS_CHANNEL).history(
                limit=100
            ):
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
        existing_subs_dict, submitters_dict, discussed_albums = get_check_data(
            masterlist
        )

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
                channel = self.bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
                sub_msg = await channel.fetch_message(error_id)
                check_msg += (
                    "\n"
                    f"**WARNING:** This album seems to be in {sub.masterlist.upper()} already. "
                    f"Link to existing submission: <{sub_msg.jump_url}>."
                )
            elif sub.warning == "user already in masterlist":
                channel = self.bot.get_channel(MASTERLIST_CHANNEL_DICT[sub.masterlist])
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

    async def _masterlist_sub_make(self, post: str, masterlist: str) -> Sub:
        """
        Create a submission from a formatted submission message in a masterlist.
        Input a string (NOT A DISCORD MESSAGE).
        """
        post_split_list = post.split("_by_")
        sub_data = [post_split_list[0]]
        post_split_list = post_split_list[1].split("(", 1)
        sub_data.append(post_split_list[0])
        post_split_list = post_split_list[1].split(")", 1)
        sub_data.append(post_split_list[0])
        post_split_list = post_split_list[1][2:].split(")")
        sub_data.append(post_split_list[0])
        sub_id = ""
        for i in post_split_list[1]:
            if i.isnumeric():
                sub_id += i
        sub_data.append(sub_id)
        user = await self.bot.fetch_user(int(sub_id))
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

    async def _update_subs_sheet(self, ctx: Context, masterlist: str) -> None:
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
        async for msg in self.bot.get_channel(
            MASTERLIST_CHANNEL_DICT[masterlist]
        ).history():
            try:
                sub = await self._masterlist_sub_make(msg.content, masterlist)
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
            except Exception as e:
                print_info(f"{type(e).__name__}: {e}")
                problem_subs.append(msg.jump_url)

        print_info(f"{masterlist.upper()} sheet updated.")
        await ctx.send(f"{masterlist.upper()} sheet updated.")

        if problem_subs:
            await ctx.send(f"Problem subs in {masterlist.upper()}:")
            await ctx.send("\n".join(problem_subs))

    async def _sheet_to_masterlist(self, ctx: Context, masterlist: str) -> None:
        """
        Pass all submissions from a sheet to its corresponding masterlist.
        """
        print_info(f"Updating {masterlist.upper()} masterlist.")

        await ctx.send(f"Updating {masterlist.upper()} masterlist.")

        channel = self.bot.get_channel(MASTERLIST_CHANNEL_DICT[masterlist])
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

        print_info(
            f"{masterlist.upper()} masterlist has been updated in a random order."
        )

        await ctx.send(
            f"{masterlist.upper()} masterlist has been updated in a random order."
        )
