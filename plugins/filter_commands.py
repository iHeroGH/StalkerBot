import logging

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client, database as db

from .stalker_utils.stalker_cache_utils import stalker_cache, \
                                            filter_modify_cache_db, get_stalker
from .stalker_utils.stalker_objects import Filter, FilterEnum
from .stalker_utils.misc import get_guild_from_cache, get_users_from_cache
from .stalker_utils.autocomplete import current_guild_autocomplete
from .stalker_utils.input_sanitizer import MIN_INPUT_LENGTH, \
                                            MAX_INPUT_LENGTH,\
                                            has_blacklisted, \
                                            get_blacklisted_error


log = logging.getLogger("plugins.filter_commands")

class FilterCommands(client.Plugin):

    # FILTER ADDITION

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

        # Constrain filter
        if len(filter) < MIN_INPUT_LENGTH:
            return await ctx.send(
                f"Text filters must be at least " +
                f"{MIN_INPUT_LENGTH} characters long."
            )
        if len(filter) > MAX_INPUT_LENGTH:
            return await ctx.send(
                f"Text filters cannot exceed " +
                f"{MAX_INPUT_LENGTH} characters long."
            )
        if has_blacklisted(filter):
            return await ctx.send(get_blacklisted_error())
        filter = filter.lower()

        log.info(f"Attempting to filter text '{filter}' from {ctx.user.id}")

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

        log.info(f"Attempting to filter user '{filter.id}' from {ctx.user.id}")

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
                channel_types=[
                    n.ChannelType.guild_text,
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

        log.info(f"Attempting to filter channel '{filter.id}' from {ctx.user.id}")

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

        log.info(f"Attempting to filter server '{filter}' from {ctx.user.id}")

        # The bot needs to be in the server
        server = get_guild_from_cache(self.bot, filter, ctx)
        if not server:
            log.info(f"Server '{filter}' not found.")
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

    # FILTER REMOVAL

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

        log.info(f"Attempting to remove text filter '{filter}' from {ctx.user.id}")

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
                " it may not already be in your list. " +
                "Make sure to select an option from the autocomplete."
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
                filter: str | int
            ) -> None:
        """Removes a user filter"""

        log.info(f"Attempting to remove user filter '{filter}' from {ctx.user.id}")

        if isinstance(filter, str):
            if filter.isdigit():
                    filter = int(filter)
            else:
                return await ctx.send(
                    "Make sure to select an option from the autocomplete."
                )

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                filter,
                FilterEnum.user_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list. " +
                "Make sure to select an option from the autocomplete."
            )

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
                filter: str | int
            ) -> None:
        """Removes a channel filter"""

        log.info(f"Attempting to remove channel filter '{filter}' from {ctx.user.id}")

        if isinstance(filter, str):
            if filter.isdigit():
                    filter = int(filter)
            else:
                return await ctx.send(
                    "Make sure to select an option from the autocomplete."
                )

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                filter,
                FilterEnum.channel_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list. " +
                "Make sure to select an option from the autocomplete."
            )

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
                filter: str | int
            ) -> None:
        """Removes a server filter"""

        log.info(f"Attempting to remove server filter '{filter}' from {ctx.user.id}")

        if isinstance(filter, str):
            if filter.isdigit():
                    filter = int(filter)
            else:
                return await ctx.send(
                    "Make sure to select an option from the autocomplete."
                )

        # Won't check if the bot is in the server already, because it is
        # valid that a user would remove a server filter after the bot is
        # removed from it
        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                filter,
                FilterEnum.server_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list. " +
                "Make sure to select an option from the autocomplete."
            )

        await ctx.send(f"Removed **{filter}**!")

    # FILTER UTILS

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
                value=str(filter.filter)
            )
            for filter in sorted(stalker.filters[filter_type])
        ]

        return choices[:25]

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
                value=str(user.id) if isinstance(user, n.GuildMember) else str(user)
            )
            for user in sorted(
                users,
                key=lambda x: x.username if isinstance(x, n.GuildMember) else str(x)
            )
        ]

        return choices[:25]

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
    async def filter_current_guild_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        return await current_guild_autocomplete(self.bot, ctx)
