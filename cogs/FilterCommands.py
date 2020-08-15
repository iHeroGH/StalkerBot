import discord
from discord.ext import commands
import asyncpg
import json


class FilterCommands(commands.Cog, name = "Filter Commands"):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command = True)
    async def filter(self, ctx, filterType, filter = None):
        """Sets a filter provided a type (can be "list" which lists all your filters)"""

        pass

    @filter.command()
    async def text(self, ctx, filter):
        """Adds a text filter"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("INSERT INTO textfilters (userid, textfilter) VALUES($1, $2);", ctx.author.id, filter)
        await connection.close()
        await ctx.send(f"Added `{filter}` to your text filter list")

    @filter.command()
    @commands.guild_only()
    async def channel(self, ctx, filter:discord.TextChannel):
        """Adds a channel filter"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("INSERT INTO channelfilters (userid, channelfilter) VALUES($1, $2);", ctx.author.id, filter.id)
        await connection.close()
        await ctx.send(f"Added {filter.mention} to your channel filter list")
                
    @filter.command(name="list")
    async def _list(self, ctx):
        """Lists all your filters"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        textRows = await connection.fetch("select * from textfilters where userid = $1;", ctx.author.id)
        channelRows = await connection.fetch("select * from channelfilters where userid = $1;", ctx.author.id)
        await connection.close()

        if len(textRows) == 0 and len(channelRows) == 0:
            await ctx.send(f"You don't have any keywords. Set some up by running the `{ctx.prefix}addkeyword` command")
            return

        textFilters = []
        channelFilters = []
        

        for i in textRows:
            textFilters.append(i['textfilter'])
        textFilters = ', '.join(textFilters)

        for i in channelRows:
            if ctx.guild.get_channel(i['channelfilter']) is not None:
                channelFilters.append(i['channelfilter'])
        channelFilters = ', '.join(channelFilters)


        await ctx.send(f"Text Filters: `{textFilters}` \n Channel Filters: {channelFilters}")


    @filter.group(invoke_without_command = True)
    async def remove(self, ctx):
        """Removes a filter (text or channel)"""
        pass

    @remove.command(name="text")
    async def _text(self, ctx, filter):
        """Removes a text filter"""

        
        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("DELETE FROM textfilters WHERE userid=$1 and textfilter=$2;", ctx.author.id, filter)
        await connection.close()

    @remove.command(name="channel")
    @commands.guild_only()
    async def _channel(self, ctx, filter:discord.TextChannel):
        """Removes a channel filter"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("DELETE FROM channelfilters WHERE userid=$1 and textfilter=$2;", ctx.author.id, filter)
        await connection.close()



def setup(bot):
    bot.add_cog(FilterCommands(bot))
