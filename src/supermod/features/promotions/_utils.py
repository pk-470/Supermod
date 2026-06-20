from discord import Colour, Embed

from supermod.features.newsletter._utils import post_split
from supermod.features.promotions._constants import *


def promo_make(promo_data: list[str]) -> Embed | str:
    """Build the formatted promo message from the promo data list."""
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
