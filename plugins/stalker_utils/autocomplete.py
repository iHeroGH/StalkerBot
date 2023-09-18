import novus as n
from novus import types as t

from .stalker_objects import Filter, FilterEnum

async def current_guild_autocomplete(
            bot,
            ctx: t.CommandI
        ) -> list[n.ApplicationCommandChoice]:
    """Retrieves an option for the current guild"""
    Filter.bot = bot

    if not ctx.guild:
        return []

    fake_filter = Filter(ctx.guild.id, FilterEnum.server_filter)
    choices = [
        n.ApplicationCommandChoice(
            name=await fake_filter.get_list_identifier(md="", mention=False),
            value=str(ctx.guild.id)
        )
    ]

    return choices