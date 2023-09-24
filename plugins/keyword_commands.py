import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client, database as db

from .stalker_utils.stalker_cache_utils import stalker_cache, \
                                            keyword_modify_cache_db, get_stalker
from .stalker_utils.misc import get_guild_from_cache
from .stalker_utils.autocomplete import current_guild_autocomplete
from .stalker_utils.input_sanitizer import MIN_INPUT_LENGTH, \
                                            MAX_INPUT_LENGTH,\
                                            has_blacklisted, \
                                            get_blacklisted_error

class KeywordCommands(client.Plugin):


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
                f"Keywords must be at least " +
                f"{MIN_INPUT_LENGTH} characters long."
            )
        if len(keyword) > MAX_INPUT_LENGTH:
            return await ctx.send(
                f"Keywords cannot exceed " +
                f"{MAX_INPUT_LENGTH} characters long."
            )
        if has_blacklisted(keyword):
            return await ctx.send(get_blacklisted_error())
        keyword = keyword.lower()

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

    @client.command(name="keyword list")
    async def list_keywords(self, ctx: t.CommandI) -> None:
        """Lists a user's keywords"""

        stalker = get_stalker(ctx.user.id)

        await ctx.send(
            embeds=[stalker.format_keywords(self.bot)]
        )

    @add_keyword.autocomplete
    @remove_keyword.autocomplete
    async def keyword_current_guild_autocomplete(
                self,
                ctx: t.CommandI
            ) -> list[n.ApplicationCommandChoice]:
        return await current_guild_autocomplete(self.bot, ctx)