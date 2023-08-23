import typing

import novus as n
from novus import types as t
from novus.ext import client

def get_guild_from_cache(
                bot: client.Client,
                server_id: str | int,
                ctx: typing.Optional[t.CommandI] = None,
            ) -> n.BaseGuild | None:
        """
        Retrieves a Guild from the bot's cache given its ID

        If "1" is passed as the ID, return the guild in which the command
        was run

        Parameters
        ----------
        bot : Client
            The Client object to check cache from
        server_id : str
            The ID of the guild to find
        ctx : t.CommandI | None
            The command interaction to find the guild from. If None is given,
            no default guild is returned.

        Returns
        -------
        guild : n.BaseGuild | None
            The guild, if it was found
        """

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