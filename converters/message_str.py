import re

from discord.ext import commands


class MessageStr(commands.Converter):

    async def convert(self, ctx, value):

        # This function accepts any string and returns the value if it is non-numeric
        if not value.isdigit():
            return str(value)

        # It didn't convert and return an argument, so we've gotta raise an error
        raise commands.BadArgument("`{0}` is a numeric value.".format(value))
