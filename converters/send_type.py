from discord.ext import commands


class SendType(commands.Converter):

    async def convert(self, ctx, value):

        # This function accepts channeltypes of 'c' and 'u'
        if value.lower() == 'c' or value.lower() == 'u':
            return value

        # It didn't convert and return an argument, so we've gotta raise an error
        raise commands.BadArgument("`{0}` isn't c or u.".format(value))
