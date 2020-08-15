import discord
from discord.ext import commands
import asyncpg


class FilterCommands(commands.Cog, name="Filter Commands"):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def filter(self, ctx):
        """Sets a filter provided a type (can be "list" which lists all your filters)"""

        await ctx.send_help(ctx.command)

    @filter.command()
    async def text(self, ctx, filter:str):
        """Adds a text filter"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("INSERT INTO textfilters (userid, textfilter) VALUES ($1, $2);", ctx.author.id, filter)
        await connection.close()
        await ctx.send(f"Added `{filter}` to your text filter list")

    @filter.command(name="channel")
    @commands.guild_only()
    async def filter_channel(self, ctx, filter:discord.TextChannel):
        """Adds a channel filter"""

        async with self.bot.datbabase() as db:
            await db("INSERT INTO channelfilters (userid, channelfilter) VALUES ($1, $2);", ctx.author.id, filter.id)
        await ctx.send(f"Added {filter.mention} to your channel filter list")

    @filter.command(name="list")
    async def filter_list(self, ctx):
        """Lists all your filters"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        textRows = await connection.fetch("SELECT * FROM textfilters WHERE userid=$1;", ctx.author.id)
        channelRows = await connection.fetch("SELECT * FROM channelfilters WHERE userid=$1;", ctx.author.id)
        await connection.close()

        if len(textRows + channelRows) == 0:
            await ctx.send(f"You don't have any keywords. Set some up by running the `{ctx.prefix}addkeyword` command")
            return

        textFilters = [i['textfilter'] for i in textRows]
        channelFilters = [o.mention for o in [ctx.guild.get_channel(i['channelfilter']) for i in channelRows] if o is not None]

        await ctx.send(f"Text Filters: `{', '.join(textFilters)}` \n Channel Filters: {', '.join(channelFilters)}")

    @filter.group(name="remove", invoke_without_command=True)
    async def filter_remove(self, ctx):
        """Removes a filter (text or channel)"""

        await ctx.send_help(ctx.command)

    @filter_remove.command(name="text")
    async def filter_remove_text(self, ctx, filter:str):
        """Removes a text filter"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("DELETE FROM textfilters WHERE userid=$1 and textfilter=$2;", ctx.author.id, filter)
        await connection.close()
        return await ctx.send("Done.")

    @filter_remove.command(name="channel")
    @commands.guild_only()
    async def filter_remove_channel(self, ctx, filter:discord.TextChannel):
        """Removes a channel filter"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("DELETE FROM channelfilters WHERE userid=$1 and textfilter=$2;", ctx.author.id, filter)
        await connection.close()
        return await ctx.send("Done.")



def setup(bot):
    bot.add_cog(FilterCommands(bot))
