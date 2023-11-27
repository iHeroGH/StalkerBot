import discord
from discord.ext import commands, vbu


class CogName(vbu.Cog, name="Help-Command Name"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=[], hidden=False)
    async def commandName(self, ctx):
        """Command help text"""
        # async with vbu.Database() as db:
            # await db("",)
        pass


def setup(bot):
    bot.add_cog(CogName(bot))
