import logging

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client

from .stalker_utils.stalker_cache_utils import stalker_cache

log = logging.getLogger("plugins.filter_commands")

class FilterCommands(client.Plugin):

    @client.command(
        name="filter add text",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add"
            ),
        ]
    )
    async def add_text_filter(self, ctx: t.CommandI, filter: str) -> None:
        """Adds a text filter"""


    @client.command(
        name="filter add user",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.user,
                description="The filter you want to add"
            ),
        ]
    )
    async def add_user_filter(self, ctx: t.CommandI, filter: n.User) -> None:
        """Adds a user filter"""
        ...

    @client.command(
        name="filter add channel",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.channel,
                description="The filter you want to add"
            ),
        ]
    )
    async def add_channel_filter(self, ctx: t.CommandI) -> None:
        """Adds a channel filter"""
        ...

    @client.command(
        name="filter add server",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add"
            ),
        ]
    )
    async def add_server_filter(self, ctx: t.CommandI) -> None:
        """Adds a server filter"""
        ...

    @client.command(
        name="filter remove text",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to remove"
            ),
        ]
    )
    async def remove_text_filter(self, ctx: t.CommandI) -> None:
        """Removes a text filter"""
        ...

    @client.command(
        name="filter remove user",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.user,
                description="The filter you want to add"
            ),
        ]
    )
    async def remove_user_filter(self, ctx: t.CommandI) -> None:
        """Removes a user filter"""
        ...

    @client.command(
        name="filter remove channel",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.channel,
                description="The filter you want to add"
            ),
        ]
    )
    async def remove_channel_filter(self, ctx: t.CommandI) -> None:
        """Removes a channel filter"""
        ...

    @client.command(
        name="filter remove server",
        options = [
            n.ApplicationCommandOption(
                name="filter",
                type=n.ApplicationOptionType.string,
                description="The filter you want to add"
            ),
        ]
    )
    async def remove_server_filter(self, ctx: t.CommandI) -> None:
        """Removes a server filter"""
        ...