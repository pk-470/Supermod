from discord.ext import commands, tasks
from discord import Message
from asyncio.exceptions import TimeoutError

from features.submissions.subs_constants import *
from features.submissions.subs_utils import *

from mode_switch import LOCAL_MODE


class Submissions(
    commands.Cog,
    name="Album Submissions",
    description="Functions to handle album submissions for the masterlists.",
):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sheet_updating = False
        self.masterlist_updating = False

        if LOCAL_MODE == "ON":
            print(
                f"{pendulum.now('America/Toronto').strftime('%Y-%m-%d %H:%M:%S EST')}: "
                + "Submission sheets will not be updated (LOCAL_MODE: ON)."
            )
        elif LOCAL_MODE == "OFF":
            self.subs_sheet_update.start()

    @tasks.loop(hours=12)
    async def subs_sheet_update(self):
        self.sheet_updating = True
        for masterlist in MASTERLIST_CHANNEL_DICT:
            await update_subs_sheet(
                self.bot, self.bot.get_channel(SUB_APPROVAL_CHANNEL), masterlist
            )
        self.sheet_updating = False

    async def updating_check(self, ctx: commands.Context):
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
    async def my_subs(self, ctx: commands.Context, masterlist=None):
        if await self.updating_check(ctx):
            return

        async def retrieve_sub(ctx: commands.Context, masterlist):
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
    @commands.has_role(STAFF_ROLE)
    async def submit(self, ctx: commands.Context):
        if await self.updating_check(ctx):
            return

        await ctx.send(
            "You have 5 minutes to respond with your submission, "
            "or with 'stop' to stop the submission process."
        )

        def check(resp: Message):
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
    @commands.has_role(STAFF_ROLE)
    async def subs(self, ctx: commands.Context, masterlist=None):
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
                "· 'ok' in order to approve all submissions without errors or warnings;\n"
                "· 'reject' followed by the numbers of the submissions you want to reject "
                "(separated by ',');\n"
                "· 'unhalt' followed by the numbers of the submissions you want to unhalt "
                "(separated by ',');\n"
                "· 'stop' in order to stop the process."
            )

        else:
            await ctx.send(
                "You have 30 minutes to respond with one of:\n"
                "· 'ok' in order to approve all submissions without errors or warnings;\n"
                "· 'reject' followed by the numbers of the submissions you want to reject "
                "(separated by ',');\n"
                "· 'halt' followed by the numbers of the submissions you want to halt "
                "for later consideration (separated by ',');\n"
                "· 'stop' in order to stop the process."
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
            elif response.content.lower().startswith("ok"):
                if masterlist == "error":
                    await ctx.send(
                        "I can't add submissions with errors to the masterlist."
                    )
                elif masterlist == "halted":
                    for _, sub in list(subs_dict.items()):
                        if type(sub).__name__ != "Sub_error" and sub.warning is None:
                            await sub.message.clear_reaction("🇭")
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
    @commands.has_role(STAFF_ROLE)
    async def get_random(self, ctx: commands.Context, masterlist=None):
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
    @commands.has_role(STAFF_ROLE)
    async def update_sheet(self, ctx: commands.Context, masterlist=None):
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
    @commands.has_role(STAFF_ROLE)
    async def update_masterlist(self, ctx: commands.Context, masterlist=None):
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
