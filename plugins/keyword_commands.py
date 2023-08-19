import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client


class KeywordCommands(client.Plugin):

    @client.command(
        name="add_keyword",
        options = []
    )
    async def add_keyword(self, ctx: t.CommandI) -> None:
        """Adds a keyword"""
        await ctx.send("Added")

    @client.command(name="remove_keyword")
    async def remove_keyword(self, ctx: t.CommandI) -> None:
        """Removes a keyword"""
        await ctx.send("Removed")

    @client.command(name="list_keywords")
    async def list_keywords(self, ctx: t.CommandI) -> None:
        """Lists a user's keywords"""
        await ctx.send("Listed")