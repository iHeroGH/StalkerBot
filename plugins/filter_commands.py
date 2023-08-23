import logging

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client, database as db

from .stalker_utils.stalker_cache_utils import stalker_cache, \
                                            filter_modify_cache_db, get_stalker
from .stalker_utils.stalker_objects import FilterEnum
from .stalker_utils.misc import get_guild_from_cache

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
                description="The filter you want to add"
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
                description="The filter you want to add"
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
            return await ctx.send("Couldn't find a valid guild.")

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

        await ctx.send(f"Filtered **{filter}**!")

    @client.command(
        name="filter remove text",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to remove"
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
                type=n.ApplicationOptionType.user,
                description="The filter you want to add"
            ),
        ]
    )
    async def remove_user_filter(
                self,
                ctx: t.CommandI,
                filter: n.User
            ) -> None:
        """Removes a user filter"""

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                filter.id,
                FilterEnum.user_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list."
            )

        await ctx.send(f"Removed **{filter}**!")

    @client.command(
        name="filter remove channel",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.channel,
                description="The filter you want to add"
            ),
        ]
    )
    async def remove_channel_filter(
                self,
                ctx: t.CommandI,
                filter: n.Channel
            ) -> None:
        """Removes a channel filter"""

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                filter.id,
                FilterEnum.channel_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list."
            )

        await ctx.send(f"Removed **{filter}**!")

    @client.command(
        name="filter remove server",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add"
            ),
        ]
    )
    async def remove_server_filter(
                self,
                ctx: t.CommandI,
                filter: str
            ) -> None:
        """Removes a server filter"""

        # The bot needs to be in the server
        server = get_guild_from_cache(self.bot, filter, ctx)
        if not server:
            return await ctx.send("Couldn't find a valid guild.")

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
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list."
            )

        await ctx.send(f"Removed **{filter}**!")

    @client.command(name="filter list")
    async def list_filters(self, ctx: t.CommandI) -> None:
        """Lists a user's filters"""

        stalker = get_stalker(ctx.user.id)

        await ctx.send(
            stalker.format_filters(self.bot)
        )