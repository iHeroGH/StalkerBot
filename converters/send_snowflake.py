import re

from discord.ext import commands


class SendSnowflake(commands.Converter):

    async def convert(self, ctx, value):

        # This function accepts any ints, and only returns a value if the int matches the format of a user or channel ID
        if re.match(r"^(<!?@|(<#)?)?(?P<ID>[0-9]{16,24})>?$", str(value)):
            return re.match(r"^(<!?@|(<#)?)?(?P<ID>[0-9]{16,24})>?$", str(value)).group("ID")

        # It didn't convert and return an argument, so we've gotta raise an error
        raise commands.BadArgument("`{0}` isn't a valid ID.".format(value))
