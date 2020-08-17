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

    @filter.command(name="text")
    async def filter_text(self, ctx, filter:str):
        """Adds a text filter"""

        # Opens a connection and inerts the text filter into the textfilters database
        async with self.bot.database() as db:
            await db("INSERT INTO textfilters (userid, textfilter) VALUES ($1, $2);", ctx.author.id, filter)
        
        await ctx.send(f"Added `{filter}` to your text filter list")

    @filter.command(name="channel")
    @commands.guild_only()
    async def filter_channel(self, ctx, filter:discord.TextChannel):
        """Adds a channel filter"""

        async with self.bot.database() as db:
            await db("INSERT INTO channelfilters (userid, channelfilter) VALUES ($1, $2);", ctx.author.id, filter.id)
        await ctx.send(f"Added {filter.mention} to your channel filter list")

    @filter.command(name="server")
    async def filter_server(self, ctx, filter:int=None):
        """Adds a server filter"""

        if filter is None:
            server = ctx.guild
        else:
            server = self.bot.get_guild(filter)

        if server is None:
            await ctx.send("You didn't provide a valid server ID")

        # Opens a connection and inerts the server filter into the serverfilters database
        async with self.bot.database() as db:
            await db("INSERT INTO serverfilters (userid, serverfilter) VALUES ($1, $2);", ctx.author.id, filter)
        
        await ctx.send(f"Added `{filter}` to your server filter list")

    @filter.command(name="user")
    async def filter_user(self, ctx, filter:int=None):
        """Adds a server filter"""

        if filter is not None:
            user = self.bot.get_member(filter)

        if user is None:
            await ctx.send("You didn't provide a valid user ID")

        # Opens a connection and inerts the user filter into the serverfilters database
        async with self.bot.database() as db:
            await db("INSERT INTO userfilters (userid, userfilter) VALUES ($1, $2);", ctx.author.id, filter)
        
        await ctx.send(f"Added `{filter}` to your user filter list")

    @filter.command(name="list")
    async def filter_list(self, ctx):
        """Lists all your filters"""

        async with self.bot.database() as db:
            textRows = await db("SELECT * FROM textfilters WHERE userid=$1;", ctx.author.id)
            channelRows = await db("SELECT * FROM channelfilters WHERE userid=$1;", ctx.author.id)
            serverRows = await db("SELECT * FROM serverfilters WHERE userid=$1;", ctx.author.id)
            userRows = await db("SELECT * FROM userfilters WHERE userid=$1;", ctx.author.id)

        if len(textRows + channelRows + serverRows + userRows) == 0:
            await ctx.send(f"You don't have any filters. Set some up by running the `{ctx.prefix}filter (type)` command")
            return

        textFilters = [i['textfilter'] for i in textRows]

        channelFilters = [o.mention for o in [ctx.guild.get_channel(i['channelfilter']) for i in channelRows] if o is not None]

        serverFilters = [i['serverfilter'] for i in serverRows]
        serverObjects = [self.bot.get_guild(o) for o in serverFilters]
        serverNames = [i.name for i in serverObjects]

        userFilters = [i['userfilter'] for i in userRows]
        userObjects = [self.bot.get_member(o) for o in userFilters]
        userNames = [i.mention for i in userObjects]

        await ctx.send(f"Text Filters: `{', '.join(textFilters)}` \n Channel Filters: {', '.join(channelFilters)} \n Server Filters: `{', '.join(serverNames)}` \n User Filters: `{', '.join(userNames)}`")

    @filter.group(name="remove", invoke_without_command=True)
    async def filter_remove(self, ctx):
        """Removes a filter (text or channel)"""

        await ctx.send_help(ctx.command)

    @filter_remove.command(name="text")
    async def filter_remove_text(self, ctx, filter:str):
        """Removes a text filter"""

        async with self.bot.database() as db:
            await db("DELETE FROM textfilters WHERE userid=$1 and textfilter=$2;", ctx.author.id, filter)
        return await ctx.send("Done.")

    @filter_remove.command(name="channel")
    @commands.guild_only()
    async def filter_remove_channel(self, ctx, filter:discord.TextChannel):
        """Removes a channel filter"""

        async with self.bot.database() as db:
            await db("DELETE FROM channelfilters WHERE userid=$1 AND channelfilter=$2;", ctx.author.id, filter.id)
        return await ctx.send("Done.")

    @filter_remove.command(name="server")
    async def filter_remove_server(self, ctx, filter:int=None):
        """Adds a server filter"""

        if filter is None:
            server = ctx.guild
        else:
            server = self.bot.get_guild(filter)

        if server is None:
            await ctx.send("You didn't provide a valid server ID")

        # Opens a connection and inerts the text filter into the serverfilters database
        async with self.bot.database() as db:
            await db("DELETE FROM serverfilters WHERE userid=$1 AND serverfilter=$2;", ctx.author.id, filter)
        
        await ctx.send("Done.")

    @filter_remove.command(name="user")
    async def filter_remove_user(self, ctx, filter:int=None):
        """Adds a server filter"""

        if filter is not None:
            user = self.bot.get_guild(filter)

        if user is None:
            await ctx.send("You didn't provide a valid user ID")

        # Opens a connection and inerts the user filter into the userfilters database
        async with self.bot.database() as db:
            await db("DELETE FROM userfilters WHERE userid=$1 AND userfilter=$2;", ctx.author.id, filter)
        
        await ctx.send("Done.")


def setup(bot):
    bot.add_cog(FilterCommands(bot))
