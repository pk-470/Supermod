from discord import Colour, Embed

from ..newsletter.news_utils import post_split
from .promo_constants import *


def promo_make(promo_data: list[str]) -> Embed | str:
    """
    Make the formatted message for the promo from the promo data (list).
    """
    # Embed
    if promo_data[1].lower().startswith("y"):
        embed = Embed(color=Colour.blue())
        posts = post_split(f"{promo_data[6]}\n\n{promo_data[3]}", 1024)
        for i, post in enumerate(posts):
            if i == 0:
                embed.add_field(name=promo_data[2], value=post, inline=False)
            else:
                embed.add_field(name="\u200b", value=post, inline=False)
        return embed
    # No embed
    return f"**{promo_data[2]}**\n\n{promo_data[3]}"
