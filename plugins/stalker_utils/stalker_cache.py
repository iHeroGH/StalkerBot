import logging

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client, database as db

from .stalker_objects import Stalker, Filter, FilterEnum, Keyword, Settings

log = logging.getLogger("plugins.stalker_utils.stalker_cache")

class StalkerCache(client.Plugin):

    stalker_cache: dict[int, Stalker] = {}

    @client.command(
        name="load",
    )
    async def load_data(
                self,
                ctx: t.CommandI,
            ) -> None:
        """Loads all the data from the database into the cache."""

        # We want a fresh cache every time we load
        self.stalker_cache.clear()

        # Get all the data from the database
        async with db.Database.acquire() as conn:
            settings_rows = await conn.fetch("SELECT * FROM user_settings")

            keyword_rows = await conn.fetch("SELECT * FROM keywords")

            text_filter_rows = await conn.fetch("SELECT * FROM text_filters")
            user_filter_rows = await conn.fetch("SELECT * FROM user_filters")
            channel_filter_rows = await conn.fetch("SELECT * FROM channel_filters")
            server_filter_rows = await conn.fetch("SELECT * FROM server_filters")

            temp_mute_rows = await conn.fetch("SELECT * FROM temp_mute")

            user_opt_out_rows = await conn.fetch("SELECT * FROM user_opt_out")

        # Add it to the cache
        log.info("Caching Settings.")
        for settings_record in settings_rows:
            user_id = settings_record['user_id']
            self.create_stalker(user_id)

            chosen_settings = Settings.from_record(settings_record)
            self.stalker_cache[user_id].settings = chosen_settings

        log.info("Caching Keywords.")
        for keyword_record in keyword_rows:
            user_id = keyword_record['user_id']
            self.create_stalker(user_id)

            keyword = Keyword.from_record(keyword_record)
            self.stalker_cache[user_id].keywords.add(keyword)

        log.info("Caching Text Filters.")
        self.cache_filters(text_filter_rows, FilterEnum.text_filter)
        log.info("Caching User Filters.")
        self.cache_filters(user_filter_rows, FilterEnum.user_filter)
        log.info("Caching Channel Filters.")
        self.cache_filters(channel_filter_rows, FilterEnum.channel_filter)
        log.info("Caching Server Filters.")
        self.cache_filters(server_filter_rows, FilterEnum.server_filter)

        log.info("Caching Mutes.")
        for mute_record in temp_mute_rows:
            user_id = mute_record['user_id']
            self.create_stalker(user_id)

            self.stalker_cache[user_id].mute_until = mute_record['unmute_at']

        log.info("Caching Opt-Outs.")
        for opt_record in user_opt_out_rows:
            user_id = opt_record['user_id']
            self.create_stalker(user_id)

            self.stalker_cache[user_id].is_opted = True

        log.info("Caching Complete!")
        log.info(self.stalker_cache)

    def create_stalker(self, user_id: int) -> None:
        """Creates an empty Stalker object if one is not found for a User ID"""
        if not user_id in self.stalker_cache:
            self.stalker_cache[user_id] = Stalker()

    def cache_filters(self, filter_rows, filter_type: FilterEnum) -> None:
        """
        Since filter caching is generally the same each time, we only
        deal with a changing filter_type
        """
        for filter_record in filter_rows:
            user_id = filter_record['user_id']
            filter = Filter(filter_record['filter'], filter_type)

            if not user_id in self.stalker_cache:
                self.stalker_cache[user_id] = Stalker()

            self.stalker_cache[user_id].filters.add(filter)
