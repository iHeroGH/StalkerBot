from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncpg.connection import Connection

from novus.ext import database as db

from .stalker_objects import Stalker, Filter, FilterEnum, Keyword, Settings

log = logging.getLogger("plugins.stalker_utils.stalker_cache_utils")
stalker_cache: dict[int, Stalker] = {}

async def load_data() -> None:
    """Loads all the data from the database into the cache."""

    # We want a fresh cache every time we load
    stalker_cache.clear()

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
        get_stalker(user_id)

        chosen_settings = Settings.from_record(settings_record)
        stalker_cache[user_id].settings = chosen_settings

    log.info("Caching Keywords.")
    for keyword_record in keyword_rows:
        await keyword_modify_cache_db(
            True,
            keyword_record['user_id'],
            keyword_record['keyword'],
            keyword_record['server_id']
        )

    log.info("Caching Text Filters.")
    await cache_filters(text_filter_rows, FilterEnum.text_filter)
    log.info("Caching User Filters.")
    await cache_filters(user_filter_rows, FilterEnum.user_filter)
    log.info("Caching Channel Filters.")
    await cache_filters(channel_filter_rows, FilterEnum.channel_filter)
    log.info("Caching Server Filters.")
    await cache_filters(server_filter_rows, FilterEnum.server_filter)

    log.info("Caching Mutes.")
    for mute_record in temp_mute_rows:
        user_id = mute_record['user_id']
        get_stalker(user_id)

        stalker_cache[user_id].mute_until = mute_record['unmute_at']

    log.info("Caching Opt-Outs.")
    for opt_record in user_opt_out_rows:
        user_id = opt_record['user_id']
        get_stalker(user_id)

        stalker_cache[user_id].is_opted = True

    log.info("Caching Complete!")
    log.info(stalker_cache)

def get_stalker(user_id: int) -> Stalker:
    """Creates an empty Stalker object if one is not found for a User ID"""
    if not user_id in stalker_cache:
        stalker_cache[user_id] = Stalker()

    return stalker_cache[user_id]

async def cache_filters(filter_rows, filter_type: FilterEnum) -> None:
    """
    Since filter caching is generally the same each time, we only
    deal with a changing filter_type
    """
    for filter_record in filter_rows:
        await filter_modify_cache_db(
            True,
            filter_record['user_id'],
            filter_record['filter'],
            filter_type
        )

async def keyword_modify_cache_db(
            is_add: bool,
            user_id: int,
            keyword_text: str,
            server_id: int,
            conn: Connection | None = None,
        ) -> bool:
    """
    Preforms an operation on the cache and optionally updates the database

    Parameters
    ----------
    is_add : bool
        Whether we are adding or removing from the cache/db
    user_id : int
        The user_id of the Stalker to update
    keyword_text : str
        The keyword to add/remove
    server_id : int
        The server_id for a server-specific keyword (or 0 for global)
        The server_id should be validated beforehand
    conn : Connection | None
        An optional DB connection. If given, a query will be run to add the
        given data to the database in addition to the cache

    Returns
    -------
    success : bool
        A state of sucess for the requested operation. If adding, return if
        the item was not already found. If removing, return if the item was
        present.
    """
    # Make sure we have a Stalker object in cache and create a keyword
    stalker = get_stalker(user_id)
    keyword = Keyword.from_record(
        {'keyword': keyword_text, 'server_id': server_id}
    )
    if server_id not in stalker.keywords:
        stalker.keywords[server_id] = set()

    # DB_QUERY[0] is what to use for remove
    # DB_QUERY[1] is what to use for add
    DB_QUERY = [
        """DELETE FROM
            keywords
            WHERE
            user_id = $1
            AND
            keyword = $2
            AND
            server_id = $3
        """,

        """INSERT INTO
            keywords
            (
                user_id,
                keyword,
                server_id
            )
            VALUES
            (
                $1,
                $2,
                $3
            )
        """
    ][int(is_add)]

    # CACHE_OPERATION[0] is what to use for remove
    # CACHE_OPERATION[1] is what to use for add
    CACHE_CHECK, CACHE_OPERATION = [
        (
            keyword in stalker_cache[user_id].keywords[server_id],
            stalker_cache[user_id].keywords[server_id].remove
        ),
        (
            keyword not in stalker_cache[user_id].keywords[server_id] and
            keyword not in stalker_cache[user_id].keywords[0],
            stalker_cache[user_id].keywords[server_id].add
        ),
    ][int(is_add)]

    # Perfrom the operation
    if CACHE_CHECK:
        CACHE_OPERATION(keyword)

        # If a database connection was given, add it to the db as well
        if conn:
            await conn.fetch(DB_QUERY, user_id, keyword_text, server_id)

    return CACHE_CHECK

async def filter_modify_cache_db(
            is_add: bool,
            user_id: int,
            filter_value: str | int,
            filter_type: FilterEnum,
            conn: Connection | None = None,
        ) -> bool:
    """
    Preforms an operation on the cache and optionally updates the database

    Parameters
    ----------
    is_add : bool
        Whether we are adding or removing from the cache/db
    user_id : int
        The user_id of the Stalker to update
    filter_value : str | int
        The value of the filter to add/remove
    filter_type : FilterEnum
        The type of filter to add/remove
    conn : Connection | None
        An optional DB connection. If given, a query will be run to add the
        given data to the database in addition to the cache

    Returns
    -------
    success : bool
        A state of sucess for the requested operation. If adding, return if
        the item was not already found. If removing, return if the item was
        present.
    """
    # Make sure we have a Stalker object in cache and create a keyword
    get_stalker(user_id)
    filter = Filter(filter_value, filter_type)

    FILTER_TABLE = {
        FilterEnum.text_filter: "text_filters",
        FilterEnum.user_filter: "user_filters",
        FilterEnum.channel_filter: "channel_filters",
        FilterEnum.server_filter: "server_filters",
    }[filter_type]

    # DB_QUERY[0] is what to use for remove
    # DB_QUERY[1] is what to use for add
    DB_QUERY = [
        """DELETE FROM
            {}
            WHERE
            user_id = $1
            AND
            filter = $2
        """,

        """INSERT INTO
            {}
            (
                user_id,
                filter
            )
            VALUES
            (
                $1,
                $2
            )
        """
    ][int(is_add)]

    # CACHE_OPERATION[0] is what to use for remove
    # CACHE_OPERATION[1] is what to use for add
    CACHE_CHECK, CACHE_OPERATION = [
        (
            filter in stalker_cache[user_id].filters[filter_type],
            stalker_cache[user_id].filters[filter_type].remove
        ),
        (
            filter not in stalker_cache[user_id].filters[filter_type],
            stalker_cache[user_id].filters[filter_type].add
        ),
    ][int(is_add)]

    # Perfrom the operation
    if CACHE_CHECK:
        CACHE_OPERATION(filter)

        # If a database connection was given, add it to the db as well
        if conn:
            log.info(DB_QUERY.format(FILTER_TABLE) + " " + str(user_id) + " " + str(filter_value))
            await conn.fetch(
                DB_QUERY.format(FILTER_TABLE),
                user_id,
                filter_value
            )

    return CACHE_CHECK