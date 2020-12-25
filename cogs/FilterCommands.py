import discord
from discord.ext import commands
import voxelbotutils as utils


class FilterCommands(utils.Cog, name="Filter Commands"):

    @utils.group(invoke_without_command=True)
    async def filter(self, ctx):
        """The parent group for the filter commands."""

        await ctx.send_help(ctx.command)


    @filter.subcommand_group(name="add", invoke_without_command=True)
    async def filter_add(self, ctx):
        """
        Sets a filter provided a type (can be "list" which lists all your filters).
        """

        await ctx.send_help(ctx.command)

    @filter_add.command(name="text")
    async def filter_add_text(self, ctx, filter:str):
        """
        Adds a text filter.
        """

        # Opens a connection and inerts the text filter into the textfilters database
        async with self.bot.database() as db:
            await db("INSERT INTO textfilters (userid, textfilter) VALUES ($1, $2);", ctx.author.id, filter)

        await ctx.send(f"Added `{filter}` to your text filter list", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @filter_add.command(name="channel")
    @commands.guild_only()
    async def filter_add_channel(self, ctx, filter:discord.TextChannel):
        """
        Adds a channel filter.
        """

        async with self.bot.database() as db:
            await db("INSERT INTO channelfilters (userid, channelfilter) VALUES ($1, $2);", ctx.author.id, filter.id)
        await ctx.send(f"Added {filter.mention} to your channel filter list")

    @filter_add.command(name="server")
    async def filter_add_server(self, ctx, filter:int=None):
        """Adds a server filter"""

        if filter is None:
            server = ctx.guild
        else:
            try:
                filter = int(filter)
            except ValueError:
                return await ctx.send("You must provide a valid server ID to filter servers")

        server = self.bot.get_guild(filter)

        if server is None:
            return await ctx.send("You didn't provide a valid server ID")

        # Opens a connection and inerts the server filter into the serverfilters database
        async with self.bot.database() as db:
            await db("INSERT INTO serverfilters (userid, serverfilter) VALUES ($1, $2);", ctx.author.id, filter)

        await ctx.send(f"Added `{filter}` to your server filter list")

    @filter_add.command(name="user")
    async def filter_add_user(self, ctx, filter:int=None):
        """Adds a server filter"""

        user = None

        if filter is not None:
            user = self.bot.get_user(filter) or await self.bot.fetch_user(filter)

        if user is None:
            await ctx.send("You didn't provide a valid user ID")
            return

        # Opens a connection and inerts the user filter into the serverfilters database
        async with self.bot.database() as db:
            await db("INSERT INTO userfilters (userid, userfilter) VALUES ($1, $2);", ctx.author.id, filter)

        await ctx.send(f"Added `{filter}` to your user filter list", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

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
        # userObjects = [self.bot.get_user(o) for o in userFilters]
        # userNames = [i.mention for i in userObjects if i is not None]
        userNames = [f"<@{uid}>" for uid in userFilters]

        # Empty Checks
        if len(textFilters) < 1:
            textFilters = ["No text filters have been set up"]
        if len(channelFilters) < 1:
            channelFilters = ["`No channel filters have been set up`"]
        if len(serverNames) < 1:
            serverNames = ["No server filters have been set up"]
        if len(userNames) < 1:
            userNames = ["No user filters have been set up"]

        await ctx.send(f"Text Filters: `{', '.join(textFilters)}` \n Channel Filters: {', '.join(channelFilters)} \n Server Filters: `{', '.join(serverNames)}` \n User Filters: `{', '.join(userNames)}`", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @filter.subcommand_group(name="remove", invoke_without_command=True)
    async def filter_remove(self, ctx):
        """Removes a filter (text or channel)"""

        await ctx.send_help(ctx.command)

    @filter_remove.command(name="text")
    async def filter_remove_text(self, ctx, filter:str):
        """Removes a text filter"""

        async with self.bot.database() as db:
            await db("DELETE FROM textfilters WHERE userid=$1 and textfilter=$2;", ctx.author.id, filter)
        return await ctx.send(f"Removed `{filter}` from your text filter list")

    @filter_remove.command(name="channel")
    @commands.guild_only()
    async def filter_remove_channel(self, ctx, filter:discord.TextChannel):
        """Removes a channel filter"""

        async with self.bot.database() as db:
            await db("DELETE FROM channelfilters WHERE userid=$1 AND channelfilter=$2;", ctx.author.id, filter.id)
        return await ctx.send(f"Removed `{filter.mention}` from your channel filter list")

    @filter_remove.command(name="server")
    async def filter_remove_server(self, ctx, filter:int=None):
        """Adds a server filter"""

        if filter is None:
            server = ctx.guild
        else:
            server = self.bot.get_guild(filter)

        if server is None:
            return await ctx.send("You didn't provide a valid server ID")

        # Opens a connection and inerts the text filter into the serverfilters database
        async with self.bot.database() as db:
            await db("DELETE FROM serverfilters WHERE userid=$1 AND serverfilter=$2;", ctx.author.id, filter)

        await ctx.send(f"You will now get messages from `{filter}` again")

    @filter_remove.command(name="user")
    async def filter_remove_user(self, ctx, filter:int=None):
        """Adds a server filter"""

        if filter is not None:
            user = self.bot.get_user(filter) or await self.bot.fetch_user(filter)

        if user is None:
            await ctx.send("You didn't provide a valid user ID")
            return

        # Opens a connection and inerts the user filter into the userfilters database
        async with self.bot.database() as db:
            await db("DELETE FROM userfilters WHERE userid=$1 AND userfilter=$2;", ctx.author.id, filter)

        await ctx.send(f"You will now get messages from `{filter}` again.")

    @utils.command()
    async def block(self, ctx, user:discord.User):
        """Blocks a given user by invoking filter user"""
        return await ctx.invoke(self.bot.get_command("filter add user"), user.id)

    @utils.command()
    async def unblock(self, ctx, user:discord.User):
        """Unblocks a given user by invoking filter remove user"""
        return await ctx.invoke(self.bot.get_command("filter remove user"), user.id)


def setup(bot):
    bot.add_cog(FilterCommands(bot))
