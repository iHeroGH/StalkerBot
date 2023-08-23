import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client


class MuteCommands(client.Plugin):

    @client.command(name="mute")
    async def mute(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="opt_out")
    async def opt_out(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="opt_in")
    async def opt_in(self, ctx: t.CommandI) -> None:
        ...