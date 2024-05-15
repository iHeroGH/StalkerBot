from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from datetime import datetime as dt

if TYPE_CHECKING:
    from asyncpg.connection import Connection
    import novus as n

from novus.ext import database as db

from .stalker_objects import Stalker, Filter, FilterEnum, Keyword, Settings

log = logging.getLogger("plugins.stalker_utils.stalker_cache_utils")
global stalker_cache
stalker_cache: dict[int, Stalker] = {}


def clear_cache():
    global stalker_cache
    for _, stalker in stalker_cache.items():
        stalker.clear()
    stalker_cache.clear()


def log_cache() -> None:
    """Logs a message of the cache"""
    global stalker_cache
    log.info(f"Cache Requested: {stalker_cache}")


async def load_data() -> None:
    """Loads all the data from the database into the cache."""
    global stalker_cache

    # We want a fresh cache every time we load
    clear_cache()

    # Get all the data from the database
    async with db.Database.acquire() as conn:
        channel_rows = await conn.fetch("SELECT * FROM stalker_channels")

        settings_rows = await conn.fetch("SELECT * FROM user_settings")

        keyword_rows = await conn.fetch("SELECT * FROM keywords")

        text_filter_rows = await conn.fetch("SELECT * FROM text_filters")
        user_filter_rows = await conn.fetch("SELECT * FROM user_filters")
        channel_filter_rows = await conn.fetch("SELECT * FROM channel_filters")
        server_filter_rows = await conn.fetch("SELECT * FROM server_filters")

        temp_mute_rows = await conn.fetch("SELECT * FROM temp_mute")

        user_opt_out_rows = await conn.fetch("SELECT * FROM user_opt_out")

    # Add it to the cache
    log.info("Caching Stalker Channels.")
    for channel_record in channel_rows:
        user_id = channel_record['user_id']
        stalker = get_stalker(user_id)

        stalker.dm_channel = channel_record['channel_id']

    log.info("Caching Settings.")
    for settings_record in settings_rows:
        user_id = settings_record['user_id']
        stalker = get_stalker(user_id)

        chosen_settings = Settings.from_record(settings_record)
        stalker.settings = chosen_settings

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
        stalker = get_stalker(user_id)

        stalker.mute_until = mute_record['unmute_at']

    log.info("Caching Opt-Outs.")
    for opt_record in user_opt_out_rows:
        user_id = opt_record['user_id']
        stalker = get_stalker(user_id)

        stalker.opted_out = True

    log.info(f"Caching Complete! {stalker_cache}")


def get_stalker(user_id: int) -> Stalker:
    """Creates an empty Stalker object if one is not found for a User ID"""
    global stalker_cache
    if user_id not in stalker_cache:
        log.info(f"Creating Stalker {user_id}")
        stalker_cache[user_id] = Stalker(user_id).clear()

    return stalker_cache[user_id]


def get_all_stalkers() -> list[Stalker]:
    global stalker_cache
    return list(stalker_cache.values())


async def cache_filters(
            filter_rows: list[dict[str, Any]],
            filter_type: FilterEnum
        ) -> None:
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
    Performs an operation on the cache and optionally updates the database

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
    log.info(
        f"{'Adding' if is_add else 'Removing'} {user_id}'s keyword" +
        f" {keyword_text} in {server_id} " + ("with DB" if conn else "")
    )

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
        """
        DELETE FROM
            keywords
        WHERE
            user_id = $1
        AND
            keyword = $2
        AND
            server_id = $3
        """,

        """
        INSERT INTO
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
            keyword in stalker.keywords[server_id],
            stalker.keywords[server_id].remove
        ),
        (
            keyword not in stalker.keywords[server_id] and
            keyword not in stalker.keywords[0],
            stalker.keywords[server_id].add
        ),
    ][int(is_add)]

    # Perfrom the operation
    if CACHE_CHECK:
        CACHE_OPERATION(keyword)

        # If a database connection was given, add it to the db as well
        if conn:
            await conn.execute(DB_QUERY, user_id, keyword_text, server_id)

    return CACHE_CHECK


async def filter_modify_cache_db(
            is_add: bool,
            user_id: int,
            filter_value: str | int,
            filter_type: FilterEnum,
            conn: Connection | None = None,
        ) -> bool:
    """
    Performs an operation on the cache and optionally updates the database

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
    log.info(
        f"{'Adding' if is_add else 'Removing'} {user_id}'s filter type " +
        f" {filter_type} value {filter_value} " + ("with DB" if conn else "")
    )

    # Make sure we have a Stalker object in cache and create a keyword
    stalker = get_stalker(user_id)
    _filter = Filter(filter_value, filter_type)

    if filter_type not in stalker.filters:
        stalker.filters[filter_type] = set()

    FILTER_TABLE = {
        FilterEnum.text_filter: "text_filters",
        FilterEnum.user_filter: "user_filters",
        FilterEnum.channel_filter: "channel_filters",
        FilterEnum.server_filter: "server_filters",
    }[filter_type]

    # DB_QUERY[0] is what to use for remove
    # DB_QUERY[1] is what to use for add
    DB_QUERY = [
        """
        DELETE FROM
            {}
        WHERE
            user_id = $1
        AND
            filter = $2
        """,

        """
        INSERT INTO
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
            _filter in stalker.filters[filter_type],
            stalker.filters[filter_type].remove
        ),
        (
            _filter not in stalker.filters[filter_type],
            stalker.filters[filter_type].add
        ),
    ][int(is_add)]

    # Perfrom the operation
    if CACHE_CHECK:
        CACHE_OPERATION(_filter)

        # If a database connection was given, add it to the db as well
        if conn:
            await conn.execute(
                DB_QUERY.format(FILTER_TABLE),
                user_id,
                filter_value
            )

    return CACHE_CHECK


async def opt_modify_cache_db(
            opting_out: bool,
            user_id: int,
            conn: Connection | None = None,
        ) -> bool:
    """
    Performs an operation on the cache and optionally updates the database

    Parameters
    ----------
    opting_out : bool
        Whether the user is opting out
    user_id : int
        The user_id of the Stalker to update
    conn : Connection | None
        An optional DB connection. If given, a query will be run to add the
        given data to the database in addition to the cache

    Returns
    -------
    success : bool
        A state of sucess for the requested operation. If opting-in, if the
        user was opted out. If opting out, if the user was opted in.
    """
    log.info(
        f"Opting for {user_id} to {opting_out} {'with DB' if conn else ''}"
    )

    # Make sure we have a Stalker object in cache
    stalker = get_stalker(user_id)

    # DB_QUERY[0] is what to use for opting in
    # DB_QUERY[1] is what to use for opting out
    DB_QUERY = [
        """
        DELETE FROM
            user_opt_out
        WHERE
            user_id = $1
        """,

        """
        INSERT INTO
            user_opt_out
            (
                user_id
            )
        VALUES
            (
                $1
            )
        """
    ][int(opting_out)]

    # CACHE_OPERATION[0] is what to use for opting in
    # CACHE_OPERATION[1] is what to use for opting out
    CACHE_CHECK = [
            stalker.opted_out,
            not stalker.opted_out,
    ][int(opting_out)]

    # Perfrom the operation
    if CACHE_CHECK:
        stalker.opted_out = opting_out

        # If a database connection was given, add it to the db as well
        if conn:
            await conn.execute(DB_QUERY, user_id)

    return CACHE_CHECK


async def mute_modify_cache_db(
            mute_until: dt | None,
            user_id: int,
            conn: Connection | None = None,
        ) -> bool:
    """
    Performs an operation on the cache and optionally updates the database

    Parameters
    ----------
    mute_until : dt | None
        A datetime of when to mute the bot until. If None, then we are unmuting
    user_id : int
        The user_id of the Stalker to update
    conn : Connection | None
        An optional DB connection. If given, a query will be run to add the
        given data to the database in addition to the cache

    Returns
    -------
    success : bool
        A state of sucess for the requested operation. If unmuting, if the user
        had the bot muted in the first place. If muting, True regardless.
    """
    log.info(
        f"Muting for {user_id} until {mute_until} {'with DB' if conn else ''}"
    )

    # Make sure we have a Stalker object in cache
    stalker = get_stalker(user_id)

    # DB_QUERY[0] is what to use for unmuting
    # DB_QUERY[1] is what to use for muting
    DB_QUERY = [
        (
            """
            DELETE FROM
                temp_mute
            WHERE
                user_id = $1
            AND
                unmute_at IS NOT NULL
            """, user_id
        ),
        (
            """
            INSERT INTO
                temp_mute
                (
                    user_id,
                    unmute_at
                )
            VALUES
                (
                    $1,
                    $2
                )
            ON CONFLICT (user_id)
            DO UPDATE
            SET
                unmute_at = $2
            """, user_id, mute_until
        )
    ][int(mute_until is not None)]

    # CACHE_OPERATION[0] is what to use for unmuting
    # CACHE_OPERATION[1] is what to use for muting
    CACHE_CHECK = [
            stalker.mute_until,
            True,
    ][int(mute_until is not None)]

    # Perfrom the operation
    if CACHE_CHECK:
        stalker.mute_until = mute_until

        # If a database connection was given, add it to the db as well
        if conn:
            await conn.execute(*DB_QUERY)

    return CACHE_CHECK


async def settings_modify_cache_db(
            user_id: int,
            setting: str,
            new_value: bool,
            conn: Connection | None = None,
        ) -> bool:
    """
    Performs an operation on the cache and optionally updates the database

    Parameters
    ----------
    user_id : int
        The user_id of the Stalker to update
    setting : str
        The setting to modify
    new_value : int | bool
        The new value to set the setting to
    conn : Connection | None
        An optional DB connection. If given, a query will be run to add the
        given data to the database in addition to the cache

    Returns
    -------
    success : bool
        A state of sucess for the requested operation. This will be False if
        the given setting string is not an available setting.
    """
    log.info(
        f"Changing Setting {setting} for {user_id} to {new_value} " +
        f"{'with DB' if conn else ''}"
    )

    # Make sure we have a Stalker object in cache
    stalker = get_stalker(user_id)

    # The query to change a variable setting
    DB_QUERY = (
        """
        INSERT INTO
            user_settings
            (
                user_id,
                {}
            )
        VALUES
            (
                $1,
                $2
            )
        ON CONFLICT
            (
                user_id
            )
        DO UPDATE SET
            {} = $2
        """
    )

    # CACHE_CHECK must be true to perform the caching and storing
    # CACHE_OPERATION is the operation to perform to actually cache the setting
    CACHE_CHECK: bool = setting in stalker.settings.VALID_FLAGS

    # Perfrom the operation
    if CACHE_CHECK:
        stalker.settings.__setattr__(setting, new_value)

        # If a database connection was given, add it to the db as well
        if conn:
            await conn.execute(
                DB_QUERY.format(setting, setting),
                user_id,
                new_value
            )

    return CACHE_CHECK


async def channel_modify_cache_db(
            channel: n.Channel,
            user_id: int,
            conn: Connection | None = None,
        ) -> bool:
    """
    Performs an operation on the cache and optionally updates the database

    Parameters
    ----------
    channel: n.Channel
        The channel to add to the stalker
    user_id : int
        The user_id of the Stalker to update
    conn : Connection | None
        An optional DB connection. If given, a query will be run to add the
        given data to the database in addition to the cache

    Returns
    -------
    success : bool
        A state of sucess for the requested operation. If unmuting, if the user
        had the bot muted in the first place. If muting, True regardless.
    """
    log.info(
        f"Adding channel {channel.id} to {user_id} " +
        f"{'with DB' if conn else ''}"
    )

    # Make sure we have a Stalker object in cache
    stalker = get_stalker(user_id)

    # DB_QUERY[0] is what to use for unmuting
    # DB_QUERY[1] is what to use for muting
    DB_QUERY = (
        """
        INSERT INTO
            stalker_channels
            (
                user_id,
                channel_id
            )
        VALUES
            (
                $1,
                $2
            )
        ON CONFLICT (user_id)
        DO UPDATE
        SET
            channel_id = $2
        """
    )

    # CACHE_CHECK must be true to perform the caching and storing
    # CACHE_OPERATION is the operation to perform to actually cache the setting
    CACHE_CHECK: bool = not stalker.dm_channel

    # Perfrom the operation
    if CACHE_CHECK:
        stalker.dm_channel = channel

        # If a database connection was given, add it to the db as well
        if conn:
            await conn.execute(
                DB_QUERY,
                user_id,
                channel.id
            )

    return CACHE_CHECK


def count_stalkers() -> int:
    """Returns how many Stalkers there are"""
    global stalker_cache
    return len(stalker_cache)


def count_keywords() -> int:
    """Returns how many keywords there are"""
    global stalker_cache
    keyword_count = 0

    for _, stalker in stalker_cache.items():
        for _, keyword_set in stalker.keywords.items():
            keyword_count += len(keyword_set)

    return keyword_count
