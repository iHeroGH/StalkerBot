import discord
from discord.ext import commands
import asyncpg
import json


class FilterCommands(commands.Cog, name = "Filter Commands"):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def filter(self, ctx, filterType, filter = None):
        """Sets a filter provided a type (can be "list" which lists all your filters)"""
        
        acceptableFilterTypes = ["text", "channel", "list"]

        if filterType in acceptableFilterTypes:
            
            if filterType == acceptableFilterTypes[0]:

                connection = await asyncpg.connect(**self.bot.database_auth)
                await connection.fetch("INSERT INTO filters (userid, textfilter) VALUES($1, $2);", ctx.author.id, filter)
                await connection.close()
                await ctx.send(f"Added `{filter}` to your filter list")
                return

            if filterType == acceptableFilterTypes[1]:

                try: 
                    self.bot.get_channel(filter.id)
                except AttributeError:
                    return await ctx.send("That isn't an existing channel")

                connection = await asyncpg.connect(**self.bot.database_auth)
                await connection.fetch("INSERT INTO filters (userid, channelfilter) VALUES($1, $2);", ctx.author.id, filter)
                await connection.close()

            if filterType == acceptableFilterTypes[2]:

                connection = await asyncpg.connect(**self.bot.database_auth)
                rows = await connection.fetch("select * from filters where userid = $1;", ctx.author.id)
                await connection.close()

                if len(rows) == 0:
                    await ctx.send(f"You don't have any keywords. Set some up by running the `{ctx.prefix}addkeyword` command")
                    return

                row = rows[0]
                textFilters = []
                channelFilters = []
                
                if row['textfilter'] is not None:
                    for i in row['textfilter']:
                        textFilters.append(i)
                if row['channelfilter'] is not None:
                    for i in row['channelfilter']:
                        channelFilters.append(i)


                await ctx.send(f"Text Filters: `{textFilters}` \n Channel Filters: `{channelFilters}`")

        else:
            await ctx.send(f"You didn't provide an acceptable filter type (`{ctx.prefix} filter (text, channnel, list) (filter)`)")


        

def setup(bot):
    bot.add_cog(FilterCommands(bot))
