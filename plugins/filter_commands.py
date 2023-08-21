import logging

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client

from .stalker_utils.stalker_cache_utils import stalker_cache

log = logging.getLogger("plugins.filter_commands")

class FilterCommands(client.Plugin):

    @client.command(name="filter add text")
    async def add_text_filter(self, ctx: t.CommandI) -> None:
        """Adds a text filter"""
        log.info(stalker_cache)

    @client.command(name="filter add user")
    async def add_user_filter(self, ctx: t.CommandI) -> None:
        """Adds a user filter"""
        ...

    @client.command(name="filter add channel")
    async def add_channel_filter(self, ctx: t.CommandI) -> None:
        """Adds a channel filter"""
        ...

    @client.command(name="filter add server")
    async def add_server_filter(self, ctx: t.CommandI) -> None:
        """Adds a server filter"""
        ...

    @client.command(name="filter remove text")
    async def remove_text_filter(self, ctx: t.CommandI) -> None:
        """Removes a text filter"""
        ...

    @client.command(name="filter remove user")
    async def remove_user_filter(self, ctx: t.CommandI) -> None:
        """Removes a user filter"""
        ...

    @client.command(name="filter remove channel")
    async def remove_channel_filter(self, ctx: t.CommandI) -> None:
        """Removes a channel filter"""
        ...

    @client.command(name="filter remove server")
    async def remove_server_filter(self, ctx: t.CommandI) -> None:
        """Removes a server filter"""
        ...