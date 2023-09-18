import logging

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client, database as db

from .stalker_utils.stalker_cache_utils import stalker_cache, \
                                            filter_modify_cache_db, get_stalker
from .stalker_utils.stalker_objects import Filter, FilterEnum
from .stalker_utils.misc import get_guild_from_cache, get_users_from_cache

log = logging.getLogger("plugins.filter_commands")

class FilterCommands(client.Plugin):

    @client.command(
        name="filter add text",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add"
            ),
        ]
    )
    async def add_text_filter(
                self,
                ctx: t.CommandI,
                filter: str
            ) -> None:
        """Adds a text filter"""

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                True,
                ctx.user.id,
                filter,
                FilterEnum.text_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble adding that filter, " +
                "it may already be in your list."
            )

        await ctx.send(f"Filtered **{filter}**!")

    @client.command(
        name="filter add user",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.user,
                description="The filter you want to add"
            ),
        ]
    )
    async def add_user_filter(
                self,
                ctx: t.CommandI,
                filter: n.User
            ) -> None:
        """Adds a user filter"""

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                True,
                ctx.user.id,
                filter.id,
                FilterEnum.user_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble adding that filter, " +
                " it may already be in your list."
            )

        await ctx.send(f"Filtered **{filter}**!")

    @client.command(
        name="filter add channel",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.channel,
                description="The filter you want to add",
                channel_types=[n.ChannelType.guild_text,
                               n.ChannelType.public_thread,
                               n.ChannelType.private_thread
                            ]
            ),
        ]
    )
    async def add_channel_filter(
                self,
                ctx: t.CommandI,
                filter: n.Channel
            ) -> None:
        """Adds a channel filter"""

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                True,
                ctx.user.id,
                filter.id,
                FilterEnum.channel_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble adding that filter, " +
                " it may already be in your list."
            )

        await ctx.send(f"Filtered **{filter}**!")

    @client.command(
        name="filter add server",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add",
                autocomplete=True
            ),
        ]
    )
    async def add_server_filter(
                self,
                ctx: t.CommandI,
                filter: str
            ) -> None:
        """Adds a server filter"""

        # The bot needs to be in the server
        server = get_guild_from_cache(self.bot, filter, ctx)
        if not server:
            return await ctx.send(
                "Couldn't find a valid guild. The bot may not be in that guild"
            )

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                True,
                ctx.user.id,
                server.id,
                FilterEnum.server_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble adding that filter, " +
                " it may already be in your list."
            )

        await ctx.send(f"Filtered **{server.name}**!")

    @client.command(
        name="filter remove text",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to remove",
                autocomplete=True
            ),
        ]
    )
    async def remove_text_filter(
                self,
                ctx: t.CommandI,
                filter: str
            ) -> None:
        """Removes a text filter"""

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                filter,
                FilterEnum.text_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list."
            )

        await ctx.send(f"Removed **{filter}**!")

    @client.command(
        name="filter remove user",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add",
                autocomplete=True
            ),
        ]
    )
    async def remove_user_filter(
                self,
                ctx: t.CommandI,
                filter: str
            ) -> None:
        """Removes a user filter"""

        # async with db.Database.acquire() as conn:
        #     success = await filter_modify_cache_db(
        #         False,
        #         ctx.user.id,
        #         filter.id,
        #         FilterEnum.user_filter,
        #         conn
        #     )

        # if not success:
        #     return await ctx.send(
        #         "Ran into some trouble removing that filter, " +
        #         " it may not already be in your list."
        #     )

        await ctx.send(f"Removed **{filter}**!")

    @client.command(
        name="filter remove channel",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add",
                autocomplete=True
            ),
        ]
    )
    async def remove_channel_filter(
                self,
                ctx: t.CommandI,
                filter: str
            ) -> None:
        """Removes a channel filter"""

        # async with db.Database.acquire() as conn:
        #     success = await filter_modify_cache_db(
        #         False,
        #         ctx.user.id,
        #         filter.id,
        #         FilterEnum.channel_filter,
        #         conn
        #     )

        # if not success:
        #     return await ctx.send(
        #         "Ran into some trouble removing that filter, " +
        #         " it may not already be in your list."
        #     )

        await ctx.send(f"Removed **{filter}**!")

    @client.command(
        name="filter remove server",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add",
                autocomplete=True
            ),
        ]
    )
    async def remove_server_filter(
                self,
                ctx: t.CommandI,
                filter: str
            ) -> None:
        """Removes a server filter"""

        # Won't check if the bot is in the server already, because it is
        # valid that a user would remove a server filter after the bot is
        # removed from it

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                True,
                ctx.user.id,
                filter,
                FilterEnum.server_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list."
            )

        await ctx.send(f"Removed **{filter}**!")

    @client.command(name="filter list")
    async def list_filters(self, ctx: t.CommandI) -> None:
        """Lists a user's filters"""

        stalker = get_stalker(ctx.user.id)

        guild_id = None
        if ctx.guild:
            guild_id = ctx.guild.id

        await ctx.send(
            embeds=[await stalker.format_filters(self.bot, guild_id)]
        )

    async def filter_autocomplete(
                self,
                ctx: t.CommandI,
                filter_type: FilterEnum
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves the autocomplete options for a given filter type"""

        stalker = get_stalker(ctx.user.id)

        guild_id = None
        if ctx.guild:
            guild_id = ctx.guild.id

        choices = [
            n.ApplicationCommandChoice(
                name=await filter.get_list_identifier(guild_id, md="", mention=False),
                value=f"{filter_type} {filter.filter}"
            )
            for filter in stalker.filters[filter_type]
        ]

        return choices

    @remove_text_filter.autocomplete
    async def text_filter_autocomplete(
                self,
                ctx: t.CommandI,
            ):
        """Retrieves autocomplete options for text filters"""
        return await self.filter_autocomplete(ctx, FilterEnum.text_filter)

    @remove_user_filter.autocomplete
    async def user_filter_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete options for user filters"""

        stalker = get_stalker(ctx.user.id)

        guild_id = None
        if ctx.guild:
            guild_id = ctx.guild.id

        users = await get_users_from_cache(
            self.bot,
            [filter.filter for filter in stalker.filters[FilterEnum.user_filter]],
            guild_id
        )

        choices = [
            n.ApplicationCommandChoice(
                name=user.username if isinstance(user, n.GuildMember) else str(user),
                value=f"{FilterEnum.user_filter} {user}"
            )
            for user in users
        ]

        return choices

    @remove_channel_filter.autocomplete
    async def channel_filter_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete options for channel filters"""
        return await self.filter_autocomplete(ctx, FilterEnum.channel_filter)

    @remove_server_filter.autocomplete
    async def server_filter_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete options for server filters"""
        return await self.filter_autocomplete(ctx, FilterEnum.server_filter)

    @add_server_filter.autocomplete
    async def current_server_filter_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves an option for the current guild"""
        Filter.bot = self.bot

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
