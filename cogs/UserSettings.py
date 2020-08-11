import discord
from discord.ext import commands
import asyncpg
import aiohttp
import json


class UserSettings(commands.Cog, name = "User Setting Commands"):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def settings(self, ctx):
        """Allows users to change settings (such as OwnTrigger and QuoteTrigger"""

        options = [
            "1\N{COMBINING ENCLOSING KEYCAP}. Would you like to trigger your own keywords?",
            "2\N{COMBINING ENCLOSING KEYCAP}. Would you like to be DMed if your keyword is said in a quote (> Message)?"
        ]

        message = await ctx.send("\n".join(options))
        await message.add_reaction("1\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("2\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")


        

def setup(bot):
    bot.add_cog(UserSettings(bot))
