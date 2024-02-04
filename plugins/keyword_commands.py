import logging

import novus as n
from novus import types as t
from novus.ext import client, database as db

from .stalker_utils.stalker_cache_utils import keyword_modify_cache_db, get_stalker
from .stalker_utils.misc_utils import get_guild_from_cache
from .stalker_utils.autocomplete import current_guild_autocomplete, \
                                        keyword_type_options
from .stalker_utils.input_sanitizer import MIN_INPUT_LENGTH, \
                                            MAX_INPUT_LENGTH,\
                                            has_blacklisted, \
                                            get_blacklisted_error

log = logging.getLogger("plugins.keyword_commands")

class KeywordCommands(client.Plugin):

    @client.event.filtered_component(r"KEYWORD_CLEAR \d+ \d .")
    async def clear_keywords_confirmation(self, ctx: t.ComponentI) -> None:
        """Confirms that a user wants to clear keywords and continues"""

        _, required_id, confirm, keyword_type = ctx.data.custom_id.split(" ")

        if int(required_id) != ctx.user.id:
            return await ctx.send(
                "You can't interact with this button, run " +
                f"{self.clear_keywords.mention} to get buttons you can press",
                ephemeral=True
            )

        if not int(confirm):
            return await ctx.send("Cancelling keyword clear!")

        # Get a flattened list of the stalker's keywords
        stalker = get_stalker(ctx.user.id)
        keywords = [
            keyword for keyword_set in stalker.keywords.values()
            for keyword in keyword_set
        ]

        # Update the cache and database
        async with db.Database.acquire() as conn:
            for keyword in keywords:

                if keyword_type == "g" and keyword.server_id:
                    continue
                if keyword_type == "s" and not keyword.server_id:
                    continue

                await keyword_modify_cache_db(
                    False,
                    ctx.user.id,
                    keyword.keyword,
                    keyword.server_id,
                    conn
                )

        # Send a confirmation message
        await ctx.send(
            f"Removed **{self.keyword_type_name(keyword_type)}** keywords."
        )

    @client.command(
        name="keyword add",
        options = [
            n.ApplicationCommandOption(
                name="keyword",
                type=n.ApplicationOptionType.string,
                description="The keyword you want to add"
            ),
            n.ApplicationCommandOption(
                name="server_id",
                type=n.ApplicationOptionType.string,
                description="The server ID for a server-specific keyword"
                            + ", or '1' to select the current guild",
                required=False,
                autocomplete=True
            )
        ]
    )
    async def add_keyword(
                self,
                ctx: t.CommandI,
                keyword: str,
                server_id: str = "0" # 0 is the identifier for a global keyword
            ) -> None:
        """Adds a keyword (optionally, a server-specific keyword)"""

        # Constrain keyword
        if len(keyword) < MIN_INPUT_LENGTH:
            return await ctx.send(
                "Keywords must be at least " +
                f"{MIN_INPUT_LENGTH} characters long."
            )
        if len(keyword) > MAX_INPUT_LENGTH:
            return await ctx.send(
                "Keywords cannot exceed " +
                f"{MAX_INPUT_LENGTH} characters long."
            )
        if has_blacklisted(keyword):
            return await ctx.send(get_blacklisted_error())
        keyword = keyword.lower()

        log.info(f"Attempting to add keyword '{keyword}' to {ctx.user.id}")

        # Constrain keyword count
        stalker = get_stalker(ctx.user.id)
        max_keywords = stalker.max_keywords
        if stalker.used_keywords >= max_keywords:
            return await ctx.send(
                f"You cannot add more than {max_keywords} keywords"
            )

        # Get a server if it's server-specific
        server = get_guild_from_cache(self.bot, server_id, ctx)
        if not server and server_id != "0":
            return await ctx.send("Couldn't find a valid guild.")

        # Update the cache and database
        async with db.Database.acquire() as conn:
            success = await keyword_modify_cache_db(
                True,
                ctx.user.id,
                keyword,
                server.id if server else 0,
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
            + (f" to **{server.name}** ({server.id})!" if server else "!")
        )

    @client.command(
        name="keyword remove",
        options = [
            n.ApplicationCommandOption(
                name="keyword",
                type=n.ApplicationOptionType.string,
                description="The keyword you want to remove"
            ),
            n.ApplicationCommandOption(
                name="server_id",
                type=n.ApplicationOptionType.string,
                description="The server ID for a server-specific keyword"
                            + ", or '1' to select the current guild",
                required=False,
                autocomplete=True
            )
        ]
    )
    async def remove_keyword(
                self,
                ctx: t.CommandI,
                keyword: str,
                server_id: str = "0"
            ) -> None:
        """Removes a keyword (optionally, a server-specific keyword)"""

        # Constrain keyword
        keyword.lower()

        # Get a server if it's server-specific
        server = get_guild_from_cache(self.bot, server_id, ctx)
        if not server and server_id != "0":
            return await ctx.send("Couldn't find a valid guild.")

        # Update the cache and database
        async with db.Database.acquire() as conn:
            success = await keyword_modify_cache_db(
                False,
                ctx.user.id,
                keyword,
                server.id if server else 0,
                conn
            )
        if not success:
            return await ctx.send(
                "Ran into some trouble removing that keyword, " +
                "it may not already be in your list."
            )

        # Send a confirmation message
        await ctx.send(
            f"Removed **{keyword}**"
            + (f" from **{server.name}** ({server.id})!" if server else "!")
        )

    @client.command(
        name="keyword clear",
        options = [
            n.ApplicationCommandOption(
                name="keyword_type",
                type=n.ApplicationOptionType.string,
                description="The type of keywords you want to remove",
                autocomplete=True
            ),
        ]
    )
    async def clear_keywords(self, ctx: t.CommandI, keyword_type: str):
        """Clears all keywords of a specified type"""

        # Ensure a correct type was chosen
        if keyword_type not in ["g", "s", "*"]:
            return await ctx.send(
                "Make sure to select an option from the autocomplete."
            )

        confirmation_components = [
            n.ActionRow(
                [
                    n.Button(
                        label="Yes",
                        style=n.ButtonStyle.green,
                        custom_id=f"KEYWORD_CLEAR {ctx.user.id} 1 {keyword_type}"
                    ),
                    n.Button(
                        label="No",
                        style=n.ButtonStyle.danger,
                        custom_id=f"KEYWORD_CLEAR {ctx.user.id} 0 {keyword_type}"
                    )
                ]
            )
        ]
        await ctx.send(
            "Are you sure you want to delete " +
            f"**{self.keyword_type_name(keyword_type)}** keywords? " +
            "(Warning: This is irreversible!)",
            components=confirmation_components
        )

    @client.command(name="keyword list")
    async def list_keywords(self, ctx: t.CommandI) -> None:
        """Lists a user's keywords"""

        stalker = get_stalker(ctx.user.id)

        await ctx.send(
            embeds=[stalker.format_keywords(self.bot)]
        )

    def keyword_type_name(self, keyword_type: str):
        """Returns a readable string defining the keyword type identifier"""
        keyword_type_map = {
            'g': "global",
            's': "server-specific",
            '*': "all"
        }

        return keyword_type_map[keyword_type.lower()]

    @add_keyword.autocomplete
    @remove_keyword.autocomplete
    async def keyword_current_guild_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        """Retrieves autocomplete option for the current guild"""
        return await current_guild_autocomplete(self.bot, ctx)

    @clear_keywords.autocomplete
    async def keyword_type_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        return await keyword_type_options()