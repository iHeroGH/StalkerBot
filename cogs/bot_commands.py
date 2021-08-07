import discord
from discord.ext import commands
import voxelbotutils as utils


class BotCommands(utils.Cog, name="Bot Commands"):

    MAXIMUM_ALLOWED_KEYWORDS = 10
    MINIMUM_KEYWORD_LENGTH = 2

    @utils.command(aliases=['keyword', 'add'])
    async def addkeyword(self, ctx, keyword:str):
        """Adds a keyword to your list of DM triggers"""

        # Checks if the keyword is too short
        if len(keyword) < self.MINIMUM_KEYWORD_LENGTH:
            return await ctx.send(f"That keyword is too short. It must be at least {self.MINIMUM_KEYWORD_LENGTH} characters")

        keyword = keyword.lower()

        # Gets the specific userID (to make sure it doesn't already have the specified keyword)
        async with self.bot.database() as db:
            rows = await db("select * from keywords where userid = $1 and keyword = $2;", ctx.author.id, keyword)

            # Checks if the user already has the keyword
            if len(rows) > 0:
                await ctx.send("You already have that as a keyword")
                return

            # Checks if the user has the maxiumum amount of keywords (10)
            rows = await db("SELECT * FROM keywords WHERE userid = $1;", ctx.author.id)
            max_keywords = await self.get_max_keywords(ctx.author)
            if len(rows) >= max_keywords:
                await ctx.send(f"You already have the maximum amount of keywords ({max_keywords}). Feel free to purchase more from {self.bot.config['command_data']['donate_link']} :)")
                return

            # Adds the keyword into the list
            await db("INSERT INTO keywords VALUES ($1, $2);", ctx.author.id, keyword)

        await ctx.send(f"Added `{keyword}` into <@{ctx.author.id}>'s list")

    @utils.command(aliases=['serverkeyword', 'addserver'])
    async def addserverkeyword(self, ctx, serverid:int, keyword:str):
        """Adds a keyword to your list of server-specific DM triggers"""

        # Checks if the server exists
        server = self.bot.get_guild(serverid)
        if server is None:
            return await ctx.send("The server ID you provided does not correspond to an existing server")

        # Checks if the keyword is too short
        if len(keyword) < self.MINIMUM_KEYWORD_LENGTH:
            return await ctx.send(f"That keyword is too short. It must be at least {self.MINIMUM_KEYWORD_LENGTH} characters")

        keyword = keyword.lower()

        # Gets the specific userID (to make sure it doesn't already have the specified keyword)
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM serverkeywords WHERE userid = $1 AND serverid = $2 AND keyword = $3;", ctx.author.id, serverid, keyword)

            # Checks if the user already has the keyword
            if len(rows) > 0:
                await ctx.send("You already have that as a keyword")
                return

            # Checks if the user has the maxiumum amount of keywords (10)
            rows = await db("SELECT * FROM serverkeywords WHERE userid = $1;", ctx.author.id)
            max_keywords = await self.get_max_keywords(ctx.author)
            if len(rows) >= max_keywords:
                await ctx.send(f"You already have the maximum amount of keywords ({max_keywords}). Feel free to purchase more from {self.bot.config['command_data']['donate_link']} :)")
                return

            # Adds the keyword into the list
            await db("INSERT INTO serverkeywords VALUES ($1, $2, $3);", ctx.author.id, serverid, keyword)

        await ctx.send(f"Added `{keyword}` into <@{ctx.author.id}>'s list")

    @utils.command(aliases=['keywordremove', 'remove'])
    async def removekeyword(self, ctx, keyword:str):
        """Removes a keyword from your list of DM triggers"""

        keyword = keyword.lower()

        # Gets the specific keyword and userID
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM keywords WHERE userid = $1 AND keyword = $2;", ctx.author.id, keyword)

            # Checks if the row is already in the list
            if len(rows) == 0:
                await ctx.send("That wasn't an existing keyword")
                return

            # Deletes the keyword
            await db("DELETE FROM keywords WHERE userid = $1 AND keyword = $2;", ctx.author.id, keyword)

        await ctx.send(f"Removed `{keyword}` from <@{ctx.author.id}>'s list")

    @utils.command(aliases=['serverkeywordremove', 'removeserver'])
    async def removeserverkeyword(self, ctx, serverid:int, keyword:str):
        """Removes a keyword from your list of server-specific DM triggers"""

        keyword = keyword.lower()

        # Gets the specific keyword and userID
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM serverkeywords WHERE userid = $1 AND serverid = $2 AND keyword = $3;", ctx.author.id, serverid, keyword)

            # Checks if the row is already in the list
            if len(rows) == 0:
                await ctx.send("That wasn't an existing keyword")
                return

            # Deletes the keyword
            await db("DELETE FROM serverkeywords WHERE userid = $1 AND serverid = $2 AND keyword = $3;", ctx.author.id, serverid, keyword)

        await ctx.send(f"Removed `{keyword}` from <@{ctx.author.id}>'s list")

    @utils.command()
    async def removeall(self, ctx, ident:str=None):
        """Removes all keywords from your list of DM triggers given an optional type (global/server)"""

        if ident is None:
            async with self.bot.database() as db:
                await db("DELETE FROM keywords WHERE userid = $1;", ctx.author.id)
                await db("DELETE FROM serverkeywords WHERE userid = $1;", ctx.author.id)
            ident = "None"

        database_option = {
            'g': "DELETE FROM keywords WHERE userid = $1;",
            's': "DELETE FROM serverkeywords WHERE userid = $1;",
            'n': None
        }[ident.lower()[0]]

        if ident.lower()[0] != "n":
            async with self.bot.database() as db:
                await db(database_option, ctx.author.id)
                await db(database_option, ctx.author.id)

        delete_type = {
            'g': "global",
            's': "server",
            'n': "all"
        }[ident.lower()[0]]

        await ctx.send(f"Removed {delete_type} keywords from <@{ctx.author.id}>'s list")

    @utils.command(aliases=['keywords', 'keywordlist', 'keywordslist', 'list'])
    async def listkeywords(self, ctx, user:discord.User=None):
        """Lists all your keywords"""
        
        # If the user isn't given, assume it's the author
        user = user or ctx.author

        # If the author is the owner, list the user's keywords
        if not (await self.bot.is_owner(ctx.author)) and ctx.author != user:
            return await ctx.send("You can only view your own keywords.")

        # Get the data from the database
        async with self.bot.database() as db:
            rows = await db("select * from keywords where userid = $1;", user.id)
        if len(rows) == 0:
            await ctx.send(f"You don't have any keywords. Set some up by running the `{ctx.prefix}addkeyword` command")
            return

        keywordList = []
        for row in rows:
            keywordList.append(row["keyword"])

        await ctx.send(', '.join(keywordList), allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @utils.command(aliases=['serverkeywords', 'serverkeywordlist', 'serverkeywordslist', 'serverlist', 'listserver', 'listservers'])
    async def listserverkeywords(self, ctx, user:discord.User=None):
        """Lists all your server-specific keywords"""

        # If the user isn't given, assume it's the author
        user = user or ctx.author

        # If the author is the owner, list the user's keywords
        if not (await self.bot.is_owner(ctx.author)) and ctx.author != user:
            return await ctx.send("You can only view your own keywords.")

        async with self.bot.database() as db:
            rows = await db("SELECT * FROM serverkeywords WHERE userid = $1;", user.id)
        if not rows:
            return await ctx.send(f"You don't have any server-specific keywords. Set some up by running the `{ctx.prefix}addkeyword` command")
            

        # Creates a list of server:keywords found in DB call
        keywordList = []
        for row in rows:
            server = self.bot.get_guild(row['serverid'])
            if server:
                keywordList.append(f"`Server: {server.name} ({server.id})` , Keyword: `{row['keyword']}`")
            keywordList.sort()

        sendableContent = "Server-Specific Keywords: "
        for i in keywordList:
            sendableContent = sendableContent + f"\n{str(i)}"

        await ctx.send(sendableContent, allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @utils.command(aliases=['max', 'maxkey', 'maxwords', 'maxkeyword', 'maxkeys', 'maxword'])
    async def maxkeywords(self, ctx):
        """Sends the maximum amount of keywords a user can have"""

        max_keywords = await self.get_max_keywords(ctx.author)

        await ctx.send(f"You can set {max_keywords} keywords. Buy more at {self.bot.config['command_data']['donate_link']} :)")


    async def get_max_keywords(self, user:discord.User):
        """Returns the max. amount of keywords a user can have based on upgrade.chat"""

        orders = await self.bot.upgrade_chat.get_orders(discord_id=user.id)
        total_purchases = 0

        for p in orders:
            for i in p.order_items:
                if i.product_name != "5x StalkerBot Keywords":
                    continue
                total_purchases += i.quantity

        keyword_max = self.MAXIMUM_ALLOWED_KEYWORDS + (total_purchases * 5)
        return keyword_max


def setup(bot):
    bot.add_cog(BotCommands(bot))
