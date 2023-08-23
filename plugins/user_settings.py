import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client


class UserSettings(client.Plugin):

    @client.command(name="settings")
    async def settings(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="quick_switch")
    async def quick_switch(self, ctx: t.CommandI) -> None:
        ...