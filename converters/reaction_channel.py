import re

from discord.ext import commands


class ReactionChannel(commands.Converter):

    async def convert(self, ctx, value):

        # This function accepts any ints, and only returns a value if the int matches the format of a channel ID
        if re.match(r"^([0-9]){16,24}$", value):
            return int(value)

        # It didn't convert and return an argument, so we've gotta raise an error
        raise commands.BadArgument("`{0}` isn't a valid ID.".format(value))
