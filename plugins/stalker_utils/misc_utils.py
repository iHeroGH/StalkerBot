from __future__ import annotations

import typing

import novus as n
from novus import types as t
from novus.ext import client

from datetime import timedelta
import re

def get_guild_from_cache(
                bot: client.Client | None,
                server_id: str | int,
                ctx: t.CommandI | t.ComponentI | None = None,
            ) -> n.BaseGuild | None:
        """
        Retrieves a Guild from the bot's cache given its ID

        If "1" is passed as the ID, return the guild in which the command
        was run

        Parameters
        ----------
        bot : Client | None
            The Client object to check cache from. If not given, we just return
            None
        server_id : str | int
            The ID of the guild to find
        ctx : t.CommandI | t.ComponentI | None
            The command interaction to find the guild from. If None is given,
            no default guild is returned.

        Returns
        -------
        guild : n.BaseGuild | None
            The guild, if it was found
        """
        if not bot:
            return None

        # If the user enters something that is not a digit, we couldn't
        # get a guild
        if isinstance(server_id, str):
            if server_id.isdigit():
                server_id = int(server_id)
            else:
                return None

        # If server_id is 0, it is a global keyword
        # If server_id is 1, it is the current guild
        # Otherwise, try to find a guild
        guild = None
        if server_id == 0:
            pass
        elif server_id == 1:
            if ctx:
                guild = ctx.guild
        elif server_id and server_id in bot.cache.guild_ids:
            guild = bot.cache.guilds[server_id]

        return guild

async def get_users_from_cache(
                bot: client.Client | None,
                user_id_values: list[str | int],
                guild_id: str | int | None = None
            ) -> list[int] | list[n.GuildMember | int]:
        """
        Fetches a list of users and returns their associated user objects or
        their ID

        Parameters
        ----------
        bot : Client | None
            The Client object to check cache from. If not given, we just return
            None
        user_id_values : list[str | int]
            The IDs of the users to find
        guild_id : str | int | None
            The guild to find the user in (default None, in which case we cannot
            find a user)

        Returns
        -------
        users_idents : list[int] | list[n.GuildMember | int]
            A list of user IDs or a mixture of members or IDs if the user was not
            found
        """
        user_ids = list(map(int, user_id_values))

        if not bot or not guild_id or guild_id not in bot.cache.guilds:
            return user_ids

        guild = bot.cache.guilds[guild_id]
        users: list[n.GuildMember] | None
        users = await guild.chunk_members(user_ids=user_ids) # type: ignore

        user_idents: dict[int, n.GuildMember | int] = {
            user_id: user_id for user_id in user_ids
        }
        if users:
            for user in users:
                user_idents[user.id] = user

        return list(user_idents.values())

def get_channel_from_cache(
                bot: client.Client | None,
                channel_id: str | int,
            ) -> n.Channel | None:
        """
        Retrieves a Channel from the bot's cache given its ID

        Parameters
        ----------
        bot : Client
            The Client object to check cache from. If not given, we just return
            None
        channel_id : str
            The ID of the channel to find

        Returns
        -------
        channel : n.Channel | None
            The channel, if it was found
        """

        if not bot:
            return None

        channel =  get_object_from_cache(channel_id, bot.cache.channels)
        assert not channel or isinstance(channel, n.Channel)
        return channel

def get_object_from_cache(
                object_id: str | int,
                cache: dict[int, n.User] | dict[int, n.Channel]
            ) -> n.User | n.Channel | None:
        """
        Retrieves an object from the bot's cache given its ID

        Parameters
        ----------
        object_id : str | int
            The ID of the object to find
        cache : dict[int, n.User] | dict[int, n.Channel]
            The cache to search. Usually found in Client.cache

        Returns
        -------
        object : n.User | n.Channel | None
            The user or channel, if it was found
        """

        # If given a string, make sure it's a digit
        if isinstance(object_id, str):
            if object_id.isdigit():
                object_id = int(object_id)
            else:
                return None

        # Default to None if we couldn't find the object
        object = None
        if object_id and object_id in cache:
            object = cache[object_id]

        return object

def get_datetime_until(time: str) -> timedelta:
    """
    Parse a duration string. If no duration qualifier is given, the default is
    days.

    Parameters
    ----------
    time : str
        The time that you want to parse.

    Returns
    -------
    delta : timedelta
        The change in time
    """

    # If a duration qualifier is not provided, assume days
    if time.isdigit():
        return timedelta(days=int(time))

    # Matches any digit followed by any of s, m, h, d, or y (seconds, month, hours, days, or year)
    pattern = r"(?:(?P<length>\d+)(?P<period>[smhdy]) *)"

    # If no match is found, the default time is 28 days
    if not re.match(f"^{pattern}+$", time):
        return timedelta(days=28)

    # Get the matches from the string
    matches = re.finditer(pattern, time.replace(' ', '').lower())
    builder = timedelta(seconds=0)

    # Loop through each match found and add their parsed time to the builder
    # This allows for entries such as '1d5h' to be added
    length_str: str
    period: str
    period_map = {
        "y": "years",
        "d": "days",
        "h": "hours",
        "m": "minutes",
        "s": "seconds",
    }
    for m in matches:
        length_str, period = m.group("length"), m.group("period")
        length = int(length_str)
        builder += timedelta(**{period_map[period[0]]: length})
    return builder