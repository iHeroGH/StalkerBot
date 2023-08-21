import logging

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client

from .stalker_cache_utils import load_data

log = logging.getLogger("plugins.stalker_utils.stalker_cache_manager")

class StalkerCacheManager(client.Plugin):

    @client.command(
        name="load",
    )
    async def load_data(
                self,
                ctx: t.CommandI,
            ) -> None:
        """Loads all the data from the database into the cache."""
        await load_data()


