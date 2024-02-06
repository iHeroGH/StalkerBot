import logging

import novus as n
from novus import types as t
from novus.ext import client

from .stalker_cache_utils import load_data, log_cache

log = logging.getLogger("plugins.stalker_utils.stalker_cache_manager")

class StalkerCacheManager(client.Plugin):

    @client.event.ready
    async def on_ready(self) -> None:
        """Loads all the data from the database into the cache."""
        await load_data()

    @client.command(
        name="load",
        guild_ids=[649715200890765342],# 208895639164026880],
        default_member_permissions=n.Permissions(manage_guild=True)
    )
    async def load_data(
                self,
                ctx: t.CommandI,
            ) -> None:
        """Loads all the data from the database into the cache."""
        await load_data()
        await ctx.send("Reloaded cache.", ephemeral=True)

    @client.command(
        name="log_cache",
        guild_ids=[649715200890765342],# 208895639164026880],
        default_member_permissions=n.Permissions(manage_guild=True)
    )
    async def log_cache(
                self,
                ctx: t.CommandI,
            ) -> None:
        """Sends a log message of the cache"""
        log_cache()
        await ctx.send("Logged to terminal.", ephemeral=True)
