import logging

import novus as n
from novus import types as t
from novus.ext import client

from .stalker_cache_utils import load_data, log_cache, log_cache_size
from .upgrade_chat_manager import UpgradeChatManager as ucm

log = logging.getLogger("plugins.stalker_utils.stalker_manager")


class StalkerManager(client.Plugin):

    @client.event.ready
    async def on_ready(self) -> None:
        """
        Loads all the data from the database into the cache
        and prepares UpgradeChat.
        """
        await load_data()
        ucm._initialize_client(
            self.bot.config.upgradeChat["client_id"],
            self.bot.config.upgradeChat["client_secret"]
        )

    @client.command(
        name="load",
        guild_ids=[649715200890765342],  # 208895639164026880],
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
        guild_ids=[649715200890765342],  # 208895639164026880],
        default_member_permissions=n.Permissions(manage_guild=True)
    )
    async def log_cache(
                self,
                ctx: t.CommandI,
            ) -> None:
        """Sends a log message of the cache"""
        log_cache()
        await ctx.send("Logged to terminal.", ephemeral=True)

    @client.command(
        name="log_cache_size",
        guild_ids=[649715200890765342],  # 208895639164026880],
        default_member_permissions=n.Permissions(manage_guild=True)
    )
    async def log_cache_size(
                self,
                ctx: t.CommandI,
            ) -> None:
        """Sends a log message of the size of the cache"""
        log_cache_size()
        await ctx.send("Logged to terminal.", ephemeral=True)
