import discord
from discord.ext import commands
import voxelbotutils as utils

class CogName(utils.Cog, name="Help-Command Name"):

    def __init__(self, bot):
        self.bot = bot

    @utils.command(aliases=[], hidden=False)
    async def commandName(self, ctx):
        '''Command help text'''
        # async with self.bot.database() as db:
            # await db("",)
        pass
        



def setup(bot):
    bot.add_cog(CogName(bot))