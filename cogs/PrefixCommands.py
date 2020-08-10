import discord
from discord.ext import commands
import asyncpg
import aiohttp
import json


class PrefixCommands(commands.Cog, name = "Prefix Commands"):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def prefix(self, ctx, prefix = None):
        """Changes the prefix of the server (or gives you the prefix set on the server)"""

        if prefix is None:
            connection = await asyncpg.connect(**self.bot.database_auth)
            prefixRows = await connection.fetch("SELECT from prefix where guildid = $1", ctx.guild.id)
            await connection.close()
            await ctx.send(f"The prefix for this server is `{prefixRows[0]['prefix']}`")
            return
            

        if ctx.author.guild_permissions.manage_guild:
            if len(prefix) > 0 and len(prefix) < 50:
                connection = await asyncpg.connect(**self.bot.database_auth)
                await connection.fetch("INSERT into prefix (guildid, prefix) VALUES ($1, $2) on conflict (guildid) do update set prefix = $2", ctx.guild.id, prefix)
                await connection.close()
                await ctx.send(f"Set prefix to `{prefix}`")

def setup(bot):
    bot.add_cog(PrefixCommands(bot))
