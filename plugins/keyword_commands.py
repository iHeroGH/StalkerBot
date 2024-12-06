from __future__ import annotations

import logging

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db

from .stalker_utils.autocomplete import (KEYWORD_TYPE_OPTIONS,
                                         available_guilds_autocomplete,
                                         available_channels_autocomplete,
                                         current_guild_autocomplete,
                                         current_channel_autocomplete,
                                         keyword_autocomplete)
from .stalker_utils.input_sanitizer import (MAX_INPUT_LENGTH, MIN_INPUT_LENGTH,
                                            get_blacklisted_error,
                                            has_blacklisted)
from .stalker_utils.misc_utils import (get_channel_from_cache,
                                       get_guild_from_cache)
from .stalker_utils.stalker_cache_utils import (channel_modify_cache_db,
                                                get_stalker,
                                                keyword_modify_cache_db)
from .stalker_utils.stalker_objects import KeywordEnum
log = logging.getLogger("plugins.keyword_commands")


class KeywordCommands(client.Plugin):

    @client.event.filtered_component(r"KEYWORD_CLEAR \d+ \d .")
    async def clear_keywords_confirmation(self, ctx: t.ComponentI) -> None:
        """Confirms that a user wants to clear keywords and continues"""

        log.info("Keyword clear confirmation sent.")

        _, required_id, confirm, keyword_type = ctx.data.custom_id.split(" ")

        if int(required_id) != ctx.user.id:
            return await ctx.send(
                "You can't interact with this button, run " +
                f"{self.clear_keywords.mention} to get buttons you can press",
                ephemeral=True
            )

        if not int(confirm):
            return await ctx.send("Cancelling keyword clear!", ephemeral=True)

        log.info(f"Clearing keywords for {ctx.user.id}")

        # Get a flattened list of the stalker's keywords
        stalker = get_stalker(ctx.user.id)
        keywords = [
            keyword for keyword_set in stalker.keywords.values()
            for keyword in keyword_set
        ]

        # Update the cache and database
        async with db.Database.acquire() as conn:
            for keyword in keywords:

                if keyword_type == "g" and not \
                        keyword.keyword_type == KeywordEnum.glob:
                    continue
                if keyword_type == "s" and not \
                        keyword.keyword_type == KeywordEnum.server_specific:
                    continue
                if keyword_type == "c" and not \
                        keyword.keyword_type == KeywordEnum.channel_specific:
                    continue

                await keyword_modify_cache_db(
                    False,
                    ctx.user.id,
                    keyword.keyword,
                    keyword.keyword_type,
                    keyword.server_id,
                    keyword.channel_id,
                    conn
                )

        # Send a confirmation message
        await ctx.send(
            f"Removed **{self.keyword_type_name(keyword_type)}** keywords.",
            ephemeral=True
        )

    @client.event.filtered_component(r"KEYWORD_REMOVE DROPDOWN")
    async def remove_keyword_event(self, ctx: t.ComponentI) -> None:
        """Deals with a user removing a keyword from the dropdown list"""

        log.info("Keyword removal dropdown option clicked.")

        _, req_id, kw, server_id, channel_id = ctx.data.values[0].value.split(
            "`"
        )
        if int(req_id) != ctx.user.id:
            return await ctx.send(
                "You can't interact with this button, run " +
                f"{self.remove_keyword.mention} to get buttons you can press",
                ephemeral=True
            )

        log.info("Removing keyword via dropdown")

        await self.remove_keyword_helper(ctx, server_id, channel_id, kw)

    @client.command(
        name="keyword add",
        options=[
            n.ApplicationCommandOption(
                name="keyword",
                type=n.ApplicationOptionType.STRING,
                description="The keyword you want to add"
            ),
            n.ApplicationCommandOption(
                name="server_id",
                type=n.ApplicationOptionType.STRING,
                description="The server ID for a server-specific keyword",
                required=False,
                autocomplete=True
            ),
            n.ApplicationCommandOption(
                name="channel_id",
                type=n.ApplicationOptionType.STRING,
                description="The channel ID for a channel-specific keyword",
                required=False,
                autocomplete=True
            )
        ]
    )
    async def add_keyword(
                self,
                ctx: t.CommandI,
                keyword: str,
                server_id: str = "0",
                channel_id: str = "0"
            ) -> None:
        """Adds a keyword (optionally, a server/channel-specific keyword)"""

        await ctx.defer(ephemeral=True)

        # Constrain keyword
        if len(keyword) < MIN_INPUT_LENGTH:
            return await ctx.send(
                "Keywords must be at least " +
                f"{MIN_INPUT_LENGTH} characters long.",
            )
        if len(keyword) > MAX_INPUT_LENGTH:
            return await ctx.send(
                "Keywords cannot exceed " +
                f"{MAX_INPUT_LENGTH} characters long.",
            )
        if has_blacklisted(keyword):
            return await ctx.send(get_blacklisted_error())
        keyword = keyword.lower()

        log.info(f"Attempting to add keyword '{keyword}' to {ctx.user.id}")

        # Constrain keyword count
        stalker = get_stalker(ctx.user.id)
        max_keywords = await stalker.max_keywords
        if stalker.used_keywords >= max_keywords:
            return await ctx.send(
                f"You cannot add more than {max_keywords} keywords",
            )

        # Get a server/channel if it's snowlfake-specific
        server = get_guild_from_cache(self.bot, server_id)
        if not server and server_id != "0":
            return await ctx.send(
                "Couldn't find a valid guild.",
            )

        channel = get_channel_from_cache(self.bot, channel_id)
        if not channel and channel_id != "0":
            return await ctx.send(
                "Couldn't find a valid channel.",
            )

        if channel and server:
            return await ctx.send(
                "You can only have either a server-specific or " +
                "channel-specific keyword, not both."
            )

        keyword_type = KeywordEnum.glob
        if server:
            keyword_type = KeywordEnum.server_specific
        if channel:
            keyword_type = KeywordEnum.channel_specific

        # Update the cache and database
        async with db.Database.acquire() as conn:
            success = await keyword_modify_cache_db(
                True,
                ctx.user.id,
                keyword,
                keyword_type,
                server.id if server else 0,
                channel.id if channel else 0,
                conn
            )

            await channel_modify_cache_db(
                await ctx.user.create_dm_channel(),
                ctx.user.id,
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble adding that keyword, " +
                "it may already be in your list."
            )

        # Send a confirmation message
        await ctx.send(
            f"Added **{keyword}**"
            + (f" to **{server.name}** ({server.id})" if server else "")
            + (f" to **{channel.name}** ({channel.id})" if channel else "")
            + "!"
        )

    @client.command(
        name="keyword remove",
        options=[
            n.ApplicationCommandOption(
                name="snowflake",
                type=n.ApplicationOptionType.STRING,
                description="The server ID or channel ID for a keyword",
                required=False,
                autocomplete=True
            ),
            n.ApplicationCommandOption(
                name="keyword",
                type=n.ApplicationOptionType.STRING,
                description="The keyword you want to remove",
                required=False,
                autocomplete=True
            ),
        ]
    )
    async def remove_keyword(
                self,
                ctx: t.CommandI,
                snowflake: str = "",
                keyword: str | None = None
            ) -> None:
        """Removes a keyword (optionally, a server/channel-specific keyword)"""

        server_id = "0"
        channel_id = "0"
        if snowflake:
            snowflake_id, snowflake_type = snowflake.split(" ")

            if snowflake_type == "s":
                server_id = snowflake_id

            if snowflake_type == "c":
                channel_id = snowflake_id

        if keyword is None:
            keyword_options = self.get_keyword_dropdown(
                ctx, server_id, channel_id
            )

            if not keyword_options:
                return await ctx.send(
                    "You don't have any keywords! Set some up by running " +
                    f"the {self.add_keyword.mention} command.",
                    ephemeral=True
                )

            return await ctx.send(
                "Select a keyword to remove:",
                components=[
                    n.ActionRow([
                        n.StringSelectMenu(
                            options=keyword_options,
                            custom_id="KEYWORD_REMOVE DROPDOWN",
                            placeholder="Keyword"
                        )
                    ])
                ], ephemeral=True
            )

        log.info("Removing keyword via command")

        await self.remove_keyword_helper(ctx, server_id, channel_id, keyword)

    async def remove_keyword_helper(
                self,
                ctx: t.CommandI | t.ComponentI,
                server_id: str,
                channel_id: str,
                keyword: str
            ) -> None:
        """
        Since keywords can be removed via the command or the dropdown,
        we need a helper function to deal with the actual removal of the
        keyword
        """
        # Constrain keyword
        keyword.lower()

        # Ensure we're only getting one type of keyword
        if server_id != "0" and channel_id != "0":
            return await ctx.send(
                "You've somehow chosen both a server " +
                "and channel specific keyword."
            )

        # Get a server if it's server-specific
        server = get_guild_from_cache(self.bot, server_id)
        if not server and server_id != "0":
            return await ctx.send(
                "Couldn't find a valid guild.",
                ephemeral=True
            )

        # Get a channel if it's channel-specific
        channel = get_channel_from_cache(self.bot, channel_id)
        if not channel and channel_id != "0":
            return await ctx.send(
                "Couldn't find a valid channel.",
                ephemeral=True
            )

        keyword_type = KeywordEnum.glob
        if server:
            keyword_type = KeywordEnum.server_specific
        if channel:
            keyword_type = KeywordEnum.channel_specific

        # Update the cache and database
        async with db.Database.acquire() as conn:
            success = await keyword_modify_cache_db(
                False,
                ctx.user.id,
                keyword,
                keyword_type,
                server.id if server else 0,
                channel.id if channel else 0,
                conn
            )
        if not success:
            return await ctx.send(
                "Ran into some trouble removing that keyword, " +
                "it may not already be in your list.", ephemeral=True
            )

        # Send a confirmation message
        await ctx.send(
            f"Removed **{keyword}**"
            + (f" from **{server.name}** ({server.id})!" if server else "!"),
            ephemeral=True
        )

    @client.command(
        name="keyword clear",
        options=[
            n.ApplicationCommandOption(
                name="keyword_type",
                type=n.ApplicationOptionType.STRING,
                description="The type of keywords you want to remove",
                choices=KEYWORD_TYPE_OPTIONS,
            ),
        ]
    )
    async def clear_keywords(self, ctx: t.CommandI, keyword_type: str):
        """Clears all keywords of a specified type"""

        # Ensure a correct type was chosen
        if keyword_type not in ["g", "s", "c", "*"]:
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
                        custom_id=(
                            f"KEYWORD_CLEAR {ctx.user.id} 1 {keyword_type}"
                        )
                    ),
                    n.Button(
                        label="No",
                        style=n.ButtonStyle.DANGER,
                        custom_id=(
                            f"KEYWORD_CLEAR {ctx.user.id} 0 {keyword_type}"
                        )
                    )
                ]
            )
        ]
        await ctx.send(
            "Are you sure you want to delete " +
            f"**{self.keyword_type_name(keyword_type)}** keywords? " +
            "(Warning: This is irreversible!)",
            components=confirmation_components,
            ephemeral=True
        )

    @client.command(name="keyword list")
    async def list_keywords(self, ctx: t.CommandI) -> None:
        """Lists a user's keywords"""
        await ctx.defer(ephemeral=True)

        stalker = get_stalker(ctx.user.id)

        await ctx.send(
            embeds=[await stalker.format_keywords(self.bot)]
        )

    def keyword_type_name(self, keyword_type: str):
        """Returns a readable string defining the keyword type identifier"""
        keyword_type_map = {
            'g': "global",
            's': "server-specific",
            'c': "channel-specific",
            '*': "all"
        }

        return keyword_type_map[keyword_type.lower()]

    def get_keyword_dropdown(
                self,
                ctx: t.CommandI,
                server_id: str,
                channel_id: str
            ) -> list[n.SelectOption]:

        stalker = get_stalker(ctx.user.id)

        keyword_options: list[n.SelectOption] = []
        for keyword_set in stalker.keywords.values():
            for keyword in keyword_set:
                if server_id != "0" and str(keyword.server_id) != server_id:
                    continue
                if channel_id != "0" and str(keyword.channel_id) != channel_id:
                    continue
                keyword_options.append(
                    n.SelectOption(
                        label=keyword.get_list_identifier(),
                        value=(
                            "KEYWORD_REMOVE`" +
                            f"{ctx.user.id}`{str(keyword)}`" +
                            f"{keyword.server_id}`{keyword.channel_id}"
                        )
                    )
                )

        return keyword_options

    @add_keyword.autocomplete
    async def keyword_currents_autocomplete(
                self,
                ctx: t.CommandI,
                options: dict[str, n.InteractionOption]
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete option for the current guild/channel"""
        if "server_id" in options and options["server_id"].focused:
            return await current_guild_autocomplete(
                self.bot, ctx
            )
        else:  # Channel-Specific
            return await current_channel_autocomplete(
                self.bot, ctx
            )

    @remove_keyword.autocomplete
    async def remove_keywords_autocomplete(
                self,
                ctx: t.CommandI,
                options: dict[str, n.InteractionOption]
            ) -> list[n.ApplicationCommandChoice]:
        """
        Retrieves autocomplete options depending on the focused field

        If the user is electing the server_id field, the guilds with keywords
        set will be shown

        Otherwise the user is selecting the keywords field, the keywords for
        that server are shown
        """
        if "snowflake" in options and options["snowflake"].focused:
            return (
                await available_guilds_autocomplete(self.bot, ctx, options)
                +
                await available_channels_autocomplete(self.bot, ctx, options)
            )

        return await keyword_autocomplete(self.bot, ctx, options)
