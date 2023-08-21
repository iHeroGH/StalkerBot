import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client


class FilterCommands(client.Plugin):

    @client.command(name="add text filter")
    async def add_text_filter(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="add user filter")
    async def add_user_filter(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="add channel filter")
    async def add_channel_filter(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="add server filter")
    async def add_server_filter(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="remove text filter")
    async def remove_text_filter(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="remove user filter")
    async def remove_user_filter(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="remove channel filter")
    async def remove_channel_filter(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="remove server filter")
    async def remove_server_filter(self, ctx: t.CommandI) -> None:
        ...


