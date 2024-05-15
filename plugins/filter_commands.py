import logging

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db

from .stalker_utils.autocomplete import (FILTER_TYPE_OPTIONS,
                                         current_guild_autocomplete,
                                         filter_autocomplete)
from .stalker_utils.input_sanitizer import (MAX_INPUT_LENGTH, MIN_INPUT_LENGTH,
                                            get_blacklisted_error,
                                            has_blacklisted)
from .stalker_utils.misc_utils import get_guild_from_cache
from .stalker_utils.stalker_cache_utils import (filter_modify_cache_db,
                                                get_stalker)
from .stalker_utils.stalker_objects import FilterEnum

log = logging.getLogger("plugins.filter_commands")


class FilterCommands(client.Plugin):

    # FILTER ADDITION

    @client.command(
        name="filter add text",
        options=[
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.STRING,
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
        _filter = filter

        # Constrain filter
        if len(_filter) < MIN_INPUT_LENGTH:
            return await ctx.send(
                "Text filters must be at least " +
                f"{MIN_INPUT_LENGTH} characters long.", ephemeral=True
            )
        if len(_filter) > MAX_INPUT_LENGTH:
            return await ctx.send(
                "Text filters cannot exceed " +
                f"{MAX_INPUT_LENGTH} characters long.", ephemeral=True
            )
        if has_blacklisted(_filter):
            return await ctx.send(get_blacklisted_error(), ephemeral=True)
        _filter = _filter.lower()

        log.info(f"Attempting to filter text '{_filter}' from {ctx.user.id}")

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                True,
                ctx.user.id,
                _filter,
                FilterEnum.text_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble adding that filter, " +
                "it may already be in your list.", ephemeral=True
            )

        await ctx.send(f"Filtered **{_filter}**!", ephemeral=True)

    @client.command(
        name="filter add user",
        options=[
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.USER,
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
        _filter = filter

        log.info(
            f"Attempting to filter user '{_filter.id}' from {ctx.user.id}"
        )

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                True,
                ctx.user.id,
                _filter.id,
                FilterEnum.user_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble adding that filter, " +
                " it may already be in your list.", ephemeral=True
            )

        await ctx.send(f"Filtered **{_filter}**!", ephemeral=True)

    @client.command(
        name="filter add channel",
        options=[
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.CHANNEL,
                description="The filter you want to add",
                channel_types=[
                    n.ChannelType.GUILD_TEXT,
                    n.ChannelType.PUBLIC_THREAD,
                    n.ChannelType.PRIVATE_THREAD
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
        _filter = filter

        log.info(
            f"Attempting to filter channel '{_filter.id}' from {ctx.user.id}"
        )

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                True,
                ctx.user.id,
                _filter.id,
                FilterEnum.channel_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble adding that filter, " +
                " it may already be in your list.", ephemeral=True
            )

        await ctx.send(f"Filtered **{_filter}**!", ephemeral=True)

    @client.command(
        name="filter add server",
        options=[
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.STRING,
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
        _filter = filter

        log.info(f"Attempting to filter server '{_filter}' from {ctx.user.id}")

        # The bot needs to be in the server
        server = get_guild_from_cache(self.bot, _filter, ctx)
        if not server:
            log.info(f"Server '{_filter}' not found.")
            return await ctx.send(
                "Couldn't find a valid guild. " +
                "The bot may not be in that guild",
                ephemeral=True
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
                " it may already be in your list.", ephemeral=True
            )

        await ctx.send(f"Filtered **{server.name}**!", ephemeral=True)

    # FILTER REMOVAL

    @client.command(
        name="filter remove text",
        options=[
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.STRING,
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
        _filter = filter

        log.info(
            f"Attempting to remove text filter '{_filter}' from {ctx.user.id}"
        )

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                _filter,
                FilterEnum.text_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list. " +
                "Make sure to select an option from the autocomplete.",
                ephemeral=True
            )

        await ctx.send(f"Removed **{_filter}**!", ephemeral=True)

    @client.command(
        name="filter remove user",
        options=[
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.STRING,
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
        _filter = filter

        log.info(
            f"Attempting to remove user filter '{_filter}' from {ctx.user.id}"
        )

        if isinstance(_filter, str):
            if _filter.isdigit():
                _filter = int(_filter)
            else:
                return await ctx.send(
                    "Make sure to select an option from the autocomplete.",
                    ephemeral=True
                )

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                _filter,
                FilterEnum.user_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list. " +
                "Make sure to select an option from the autocomplete.",
                ephemeral=True
            )

        await ctx.send(f"Removed **{_filter}**!", ephemeral=True)

    @client.command(
        name="filter remove channel",
        options=[
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.STRING,
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
        _filter = filter

        log.info(
            "Attempting to remove channel filter" +
            f"'{_filter}' from {ctx.user.id}"
        )

        if isinstance(_filter, str):
            if _filter.isdigit():
                _filter = int(_filter)
            else:
                return await ctx.send(
                    "Make sure to select an option from the autocomplete.",
                    ephemeral=True
                )

        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                _filter,
                FilterEnum.channel_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list. " +
                "Make sure to select an option from the autocomplete.",
                ephemeral=True
            )

        await ctx.send(f"Removed **{_filter}**!", ephemeral=True)

    @client.command(
        name="filter remove server",
        options=[
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.STRING,
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
        _filter = filter

        log.info(
            "Attempting to remove server filter" +
            f"'{_filter}' from {ctx.user.id}"
        )

        if isinstance(_filter, str):
            if _filter.isdigit():
                _filter = int(_filter)
            else:
                return await ctx.send(
                    "Make sure to select an option from the autocomplete.",
                    ephemeral=True
                )

        # Won't check if the bot is in the server already, because it is
        # valid that a user would remove a server filter after the bot is
        # removed from it
        async with db.Database.acquire() as conn:
            success = await filter_modify_cache_db(
                False,
                ctx.user.id,
                _filter,
                FilterEnum.server_filter,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble removing that filter, " +
                " it may not already be in your list. " +
                "Make sure to select an option from the autocomplete.",
                ephemeral=True
            )

        await ctx.send(f"Removed **{_filter}**!", ephemeral=True)

    @client.command(
        name="filter clear",
        options=[
            n.ApplicationCommandOption(
                name="filter_type",
                type=n.ApplicationOptionType.STRING,
                description="The type of filters you want to remove",
                choices=FILTER_TYPE_OPTIONS
            ),
        ]
    )
    async def clear_filters(self, ctx: t.CommandI, filter_type: str):
        """Clears all filters of a specified type"""

        # Ensure a correct type was chosen
        if filter_type not in ["t", "u", "c", "s", "*"]:
            return await ctx.send(
                "Make sure to select an option from the autocomplete.",
                ephemeral=True
            )

        confirmation_components = [
            n.ActionRow(
                [
                    n.Button(
                        label="Yes",
                        style=n.ButtonStyle.GREEN,
                        custom_id=f"FILTER_CLEAR {ctx.user.id} 1 {filter_type}"
                    ),
                    n.Button(
                        label="No",
                        style=n.ButtonStyle.DANGER,
                        custom_id=f"FILTER_CLEAR {ctx.user.id} 0 {filter_type}"
                    )
                ]
            )
        ]
        await ctx.send(
            "Are you sure you want to delete " +
            f"**{self.filter_type_name(filter_type)}** filters? " +
            "(Warning: This is irreversible!)",
            components=confirmation_components,
            ephemeral=True
        )

    @client.event.filtered_component(r"FILTER_CLEAR \d+ \d .")
    async def clear_filters_confirmation(self, ctx: t.ComponentI) -> None:
        """Confirms that a user wants to clear filters and continues"""

        _, required_id, confirm, filter_type = ctx.data.custom_id.split(" ")

        if int(required_id) != ctx.user.id:
            return await ctx.send(
                "You can't interact with this button, run " +
                f"{self.clear_filters.mention} to get buttons you can press",
                ephemeral=True
            )

        if not int(confirm):
            return await ctx.send("Cancelling filter clear!", ephemeral=True)

        # Get a flattened list of the stalker's filters
        stalker = get_stalker(ctx.user.id)
        filters = [
            _filter for filter_set in stalker.filters.values()
            for _filter in filter_set
        ]

        # Update the cache and database
        async with db.Database.acquire() as conn:
            for _filter in filters:

                if _filter.filter_type != self.filter_type_object(filter_type)\
                        and filter_type != "*":
                    continue

                await filter_modify_cache_db(
                    False,
                    ctx.user.id,
                    _filter.filter,
                    _filter.filter_type,
                    conn
                )

        # Send a confirmation message
        await ctx.send(
            f"Removed **{self.filter_type_name(filter_type)}** filters.",
            ephemeral=True
        )

    # FILTER UTILS

    @client.command(name="filter list")
    async def list_filters(self, ctx: t.CommandI) -> None:
        """Lists a user's filters"""

        stalker = get_stalker(ctx.user.id)

        guild_id = None
        if ctx.guild:
            guild_id = ctx.guild.id

        await ctx.send(
            embeds=[await stalker.format_filters(self.bot, guild_id)],
            ephemeral=True
        )

    def filter_type_name(self, filter_type: str) -> str:
        """Returns a readable string defining the filter type identifier"""
        filter_type_map = {
            't': "text",
            'u': "user",
            'c': "channel",
            's': "server",
            '*': "all"
        }

        return filter_type_map[filter_type.lower()]

    def filter_type_object(self, filter_type: str) -> FilterEnum:
        """Returns a FilterEnum defining the filter type identifier"""
        filter_type_map = {
            't': FilterEnum.text_filter,
            'u': FilterEnum.user_filter,
            'c': FilterEnum.channel_filter,
            's': FilterEnum.server_filter,
            '*': FilterEnum
        }

        return filter_type_map[filter_type.lower()]

    @remove_text_filter.autocomplete
    async def text_filter_autocomplete(
                self,
                ctx: t.CommandI,
                options: dict[str, n.InteractionOption]
            ):
        """Retrieves autocomplete options for text filters"""
        return await filter_autocomplete(
            ctx, FilterEnum.text_filter, options
        )

    @remove_user_filter.autocomplete
    async def user_filter_autocomplete(
                self,
                ctx: t.CommandI,
                options: dict[str, n.InteractionOption]
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete options for user filters"""
        return await filter_autocomplete(
            ctx, FilterEnum.user_filter, options, self.bot
        )

    @remove_channel_filter.autocomplete
    async def channel_filter_autocomplete(
                self,
                ctx: t.CommandI,
                options: dict[str, n.InteractionOption]
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete options for channel filters"""
        return await filter_autocomplete(
            ctx, FilterEnum.channel_filter, options
        )

    @remove_server_filter.autocomplete
    async def server_filter_autocomplete(
                self,
                ctx: t.CommandI,
                options: dict[str, n.InteractionOption]
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete options for server filters"""
        return await filter_autocomplete(
            ctx, FilterEnum.server_filter, options
        )

    @add_server_filter.autocomplete
    async def filter_current_guild_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete option for the current guild"""
        return await current_guild_autocomplete(self.bot, ctx)
