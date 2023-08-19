import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client


class KeywordCommands(client.Plugin):

    MAX_KEYWORDS = 5
    MIN_KEYWORD_LENGTH = 2

    @client.command(
        name="add",
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
                server_id: str | None = None
            ) -> None:
        """Adds a keyword (optionally, a server-specific keyword)"""

        if len(keyword) < self.MIN_KEYWORD_LENGTH:
            return await ctx.send(
                f"Keywords must be at least {self.MIN_KEYWORD_LENGTH} long."
            )
        keyword.lower()

        server = self.get_guild_from_cache(ctx, server_id)
        if server_id and not server:
            return await ctx.send("Couldn't find a valid guild.")

        await ctx.send(f"Added {keyword}" + (f" to {server.id}" if server else ""))

    @client.command(
        name="remove",
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
                server_id: str | None = None
            ) -> None:
        """Removes a keyword (optionally, a server-specific keyword)"""

        server = self.get_guild_from_cache(ctx, server_id)
        if server_id and not server:
            return await ctx.send("Couldn't find a valid guild.")

        await ctx.send(f"Removed {keyword}" + (f" from {server.id}" if server else ""))


    @client.command(name="list")
    async def list_keywords(self, ctx: t.CommandI) -> None:
        """Lists a user's keywords"""
        await ctx.send("Listed")

    def get_guild_from_cache(
                self,
                ctx: t.CommandI,
                server_id: str | None
            ) -> n.BaseGuild | None:
        """
        Retrieves a Guild from the bot's cache given its ID

        If "1" is passed as the ID, return the guild in which the command
        was run

        Parameters
        ----------
        ctx : t.CommandI
            The command interaction to find the guild from
        server_id : str
            The ID of the guild to find

        Returns
        -------
        guild : n.BaseGuild | None
            The guild, if it was found

        """
        guild = None
        if server_id == "1":
            guild = ctx.guild
        elif server_id and int(server_id) in self.bot.cache.guild_ids:
            guild = self.bot.cache.guilds[int(server_id)]

        return guild