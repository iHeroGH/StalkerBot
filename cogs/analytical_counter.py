import aiohttp
import discord
from discord.ext import commands, vbu


class AnalyticalCounter(vbu.Cog, name="Analytical Counter"):

    @vbu.command(aliases=['countservers'])
    @commands.is_owner()
    async def countguilds(self, ctx):
        """Counts how many guilds have the bot"""

        await ctx.send(f"The bot is in `{len(self.bot.guilds)}` guilds.")

    @vbu.command()
    @commands.is_owner()
    async def countusers(self, ctx):
        """Counts how many unique user IDs there are"""

        async with vbu.Database() as db:
            distinct_rows = await db("SELECT DISTINCT userid FROM keywords;")
            rows = await db("SELECT * FROM keywords;")

        await ctx.send(f"`{len(distinct_rows)}` unique users with `{len(rows)}` keywords in total.")


def setup(bot):
    bot.add_cog(AnalyticalCounter(bot))
