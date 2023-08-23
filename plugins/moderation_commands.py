import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client


class ModerationCommands(client.Plugin):

    @client.command(name="admin_keywords")
    async def admin_keywords(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="admin_filters")
    async def admin_filters(self, ctx: t.CommandI) -> None:
        ...