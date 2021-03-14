import discord
from discord.ext import commands
import voxelbotutils as utils


class SchloppCog(utils.Cog, name="SchloppShowingHisLove"):

    def __init__(self, bot):
        self.bot = bot

    @utils.command(hidden=True)    
    async def takegeorgeoutfordinner(self, ctx):
        """Takes george out to dinner"""
        
        #Dont want everyone using this.
        if ctx.author.id != 393305855929483264 and ctx.author.id != 322542134546661388:
            return
        
        with utils.Embed(use_random_colour=True) as embed:
            embed.description = "You take george out for a nice, romantic date in a fancy restaurant."

        await ctx.send(embed=embed)





def setup(bot):
    bot.add_cog(SchloppCog(bot))
