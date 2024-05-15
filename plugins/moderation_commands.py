import novus as n
from novus import types as t
from novus.ext import client

from .stalker_utils.stalker_cache_utils import get_stalker


class ModerationCommands(client.Plugin):

    @client.command(
        name="admin keywords",
        options=[
            n.ApplicationCommandOption(
                name="target",
                type=n.ApplicationOptionType.USER,
                description="The user whose keywords you want to access"
            ),
        ],
        guild_ids=[649715200890765342],  # 208895639164026880],
        default_member_permissions=n.Permissions(manage_guild=True)
    )
    async def admin_keywords(self, ctx: t.CommandI, target: n.User) -> None:
        """Lists another user's keywords"""
        stalker = get_stalker(target.id)

        await ctx.send(
            embeds=[stalker.format_keywords(self.bot)],
            ephemeral=True
        )

    @client.command(
        name="admin filters",
        options=[
            n.ApplicationCommandOption(
                name="target",
                type=n.ApplicationOptionType.USER,
                description="The user whose filters you want to access"
            ),
        ],
        guild_ids=[649715200890765342],  # 208895639164026880],
        default_member_permissions=n.Permissions(manage_guild=True)
    )
    async def admin_filters(self, ctx: t.CommandI, target: n.User) -> None:
        """Lists another user's filters"""
        stalker = get_stalker(target.id)

        guild_id = None
        if ctx.guild:
            guild_id = ctx.guild.id

        await ctx.send(
            embeds=[await stalker.format_filters(self.bot, guild_id)],
            ephemeral=True
        )
