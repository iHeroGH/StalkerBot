import typing

import novus as n
from novus import types as t
from novus.ext import client

def get_guild_from_cache(
                bot: client.Client | None,
                server_id: str | int,
                ctx: typing.Optional[t.CommandI] = None,
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
        ctx : t.CommandI | None
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

def get_user_from_cache(
                bot: client.Client | None,
                user_id: str | int,
            ) -> n.User | None:
        """
        Retrieves a User from the bot's cache given its ID

        Parameters
        ----------
        bot : Client | None
            The Client object to check cache from. If not given, we just return
            None
        user_id : str
            The ID of the user to find

        Returns
        -------
        user : n.User | None
            The user, if it was found
        """

        if not bot:
            return

        user = get_object_from_cache(user_id, bot.cache.users)
        assert not user or isinstance(user, n.User)
        return user

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
            return

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