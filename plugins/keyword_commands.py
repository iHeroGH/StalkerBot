import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client, database as db

from .stalker_utils.stalker_cache_utils import stalker_cache, \
                                            keyword_modify_cache_db
from .stalker_utils.misc import get_guild_from_cache

class KeywordCommands(client.Plugin):

    MAX_KEYWORDS = 5
    MIN_KEYWORD_LENGTH = 2
    MAX_KEYWORD_LENGTH = 150

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
                required=False
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
        if len(keyword) < self.MIN_KEYWORD_LENGTH:
            return await ctx.send(
                f"Keywords must be at least {self.MIN_KEYWORD_LENGTH} characters long."
            )
        if len(keyword) > self.MAX_KEYWORD_LENGTH:
            return await ctx.send(
                f"Keywords cannot exceed {self.MAX_KEYWORD_LENGTH} characters long."
            )
        keyword.lower()

        # Get a server if it's server-specific
        server = get_guild_from_cache(self.bot, ctx, server_id)
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
                required=False
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
        server = get_guild_from_cache(self.bot, ctx, server_id)
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

    @client.command(name="keyword list")
    async def list_keywords(self, ctx: t.CommandI) -> None:
        """Lists a user's keywords"""
        await ctx.send(str(stalker_cache[ctx.user.id].keywords))