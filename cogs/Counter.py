import aiohttp
import discord
from discord.ext import commands
import voxelbotutils as utils


class Counter(utils.Cog, name="Analytical Counter"):

    @utils.command(aliases=['countservers'])
    @commands.is_owner()
    async def countguilds(self, ctx):
        """Counts how many guilds have the bot"""

        await ctx.send(f"The bot is in `{len(self.bot.guilds)}` guilds.")

    @utils.command()
    @commands.is_owner()
    async def countusers(self, ctx):
        """Counts how many unique user IDs there are"""

        async with self.bot.database() as db:
            distinctRows = await db("SELECT DISTINCT userid FROM keywords;")
            rows = await db("SELECT * FROM keywords;")

        await ctx.send(f"`{len(distinctRows)}` unique users with `{len(rows)}` keywords in total.")


def setup(bot):
    bot.add_cog(Counter(bot))
