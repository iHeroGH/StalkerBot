import discord
from discord.ext import commands
import voxelbotutils as utils


class BotCommands(utils.Cog, name="Bot Commands"):

    MAXIMUM_ALLOWED_KEYWORDS = 5
    MINIMUM_KEYWORD_LENGTH = 2

    @utils.command(aliases=['keyword', 'addkeyword'])
    async def add(self, ctx: utils.Context, keyword: str):
        """Adds a keyword to your list of DM triggers"""

        # Checks if the keyword is too short
        if len(keyword) < self.MINIMUM_KEYWORD_LENGTH:
            return await ctx.send(f"That keyword is too short. It must be at least {self.MINIMUM_KEYWORD_LENGTH} characters")

        keyword = keyword.lower()

        # Gets the specific userID (to make sure it doesn't already have the specified keyword)
        async with self.bot.database() as db:
            keyword_exists = await db("SELECT * FROM keywords WHERE userid = $1 AND keyword = $2;", ctx.author.id, keyword)

            # Checks if the user already has the keyword
            if keyword_exists:
                return await ctx.send("You already have that as a keyword")

            # Checks if the user has the maxiumum amount of keywords (10)
            server_keyword_count = await db("SELECT COUNT(*) FROM serverkeywords WHERE userid = $1;", ctx.author.id)
            keyword_count = await db("SELECT COUNT(*) FROM keywords WHERE userid = $1;", ctx.author.id)
            max_keywords = await self.get_max_keywords(ctx.author)
            if keyword_count[0]['count'] + server_keyword_count[0]['count'] >= max_keywords:
                return await ctx.send(f"You already have the maximum amount of keywords ({max_keywords}). Purchase more from {self.bot.config['bot_info']['links']['Donate']['url']} :)")
                
            # Adds the keyword into the list
            await db("INSERT INTO keywords (userid, keyword) VALUES ($1, $2);", ctx.author.id, keyword)

        await ctx.send(f"Added `{keyword}` into <@{ctx.author.id}>'s list")

    @utils.command(aliases=['serverkeyword', 'addserverkeyword'])
    async def addserver(self, ctx: utils.Context, server_id: int, keyword: str):
        """Adds a keyword to your list of server-specific DM triggers"""

        # Checks if the server exists
        server = self.bot.get_guild(server_id)
        if not server:
            return await ctx.send("I couldn't find a server with the given ID.")

        # Checks if the keyword is too short
        if len(keyword) < self.MINIMUM_KEYWORD_LENGTH:
            return await ctx.send(f"That keyword is too short. It must be at least {self.MINIMUM_KEYWORD_LENGTH} characters")

        keyword = keyword.lower()

        # Gets the specific userID (to make sure it doesn't already have the specified keyword)
        async with self.bot.database() as db:
            keyword_exists = await db("SELECT * FROM serverkeywords WHERE userid = $1 AND serverid = $2 AND keyword = $3;", ctx.author.id, server_id, keyword)

            # Checks if the user already has the keyword
            if keyword_exists:
                return await ctx.send("You already have that as a keyword on this server.")

            # Checks if the user has the maxiumum amount of keywords (10)
            server_keyword_count = await db("SELECT COUNT(*) FROM serverkeywords WHERE userid = $1;", ctx.author.id)
            keyword_count = await db("SELECT COUNT(*) FROM keywords WHERE userid = $1;", ctx.author.id)
            max_keywords = await self.get_max_keywords(ctx.author)
            if keyword_count[0]['count'] + server_keyword_count[0]['count'] >= max_keywords:
                return await ctx.send(f"You already have the maximum amount of keywords ({max_keywords}). Purchase more from {self.bot.config['bot_info']['links']['Donate']['url']} :)")

            # Adds the keyword into the list
            await db("INSERT INTO serverkeywords (userid, serverid, keyword) VALUES ($1, $2, $3);", ctx.author.id, server_id, keyword)

        await ctx.send(f"Added `{keyword}` into <@{ctx.author.id}>'s list")

    @utils.command(aliases=['keywordremove', 'removekeyword'])
    async def remove(self, ctx: utils.Context, keyword: str):
        """Removes a keyword from your list of DM triggers"""

        keyword = keyword.lower()

        # Gets the specific keyword and userID
        async with self.bot.database() as db:
            keyword_exists = await db("SELECT * FROM keywords WHERE userid = $1 AND keyword = $2;", ctx.author.id, keyword)

            # Checks if the row is already in the list
            if not keyword_exists:
                return await ctx.send("That wasn't an existing keyword")

            # Deletes the keyword
            await db("DELETE FROM keywords WHERE userid = $1 AND keyword = $2;", ctx.author.id, keyword)

        await ctx.send(f"Removed `{keyword}` from <@{ctx.author.id}>'s list")

    @utils.command(aliases=['serverkeywordremove', 'removeserver'])
    async def removeserverkeyword(self, ctx: utils.Context, server_id: int, keyword: str):
        """Removes a keyword from your list of server-specific DM triggers"""

        keyword = keyword.lower()

        # Gets the specific keyword and userID
        async with self.bot.database() as db:
            keyword_exists = await db("SELECT * FROM serverkeywords WHERE userid = $1 AND serverid = $2 AND keyword = $3;", ctx.author.id, server_id, keyword)

            # Checks if the row is already in the list
            if not keyword_exists:
                return await ctx.send("That wasn't an existing keyword")

            # Deletes the keyword
            await db("DELETE FROM serverkeywords WHERE userid = $1 AND serverid = $2 AND keyword = $3;", ctx.author.id, server_id, keyword)

        await ctx.send(f"Removed `{keyword}` from <@{ctx.author.id}>'s list")

    @utils.command()
    async def removeall(self, ctx: utils.Context, ident: str=None):
        """Removes all keywords from your list of DM triggers given an optional type (global/server)"""

        if not ident:
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

        delete_type = {
            'g': "global",
            's': "server",
            'n': "all"
        }[ident.lower()[0]]

        await ctx.send(f"Removed {delete_type} keywords from <@{ctx.author.id}>'s list")

    @utils.command(aliases=['keywords', 'keywordlist', 'keywordslist', 'listkeywords'])
    async def list(self, ctx: utils.Context, user:discord.User=None):
        """Lists all your keywords"""
        
        # If the user isn't given, assume it's the author
        user = user or ctx.author

        # If the author is the owner, list the user's keywords
        if not (await self.bot.is_owner(ctx.author)) and ctx.author != user:
            return await ctx.send("You can only view your own keywords.")

        # Get the data from the database
        async with self.bot.database() as db:
            keyword_rows = await db("SELECT * FROM keywords WHERE userid = $1;", user.id)
            server_keyword_rows = await db("SELECT * FROM serverkeywords WHERE userid = $1;", user.id)

        # Count the keywords
        keyword_count = len(keyword_rows) + len(server_keyword_rows)
        max_keywords = await self.get_max_keywords(user)
        total_keywords_message = f"{user.mention} is using {keyword_count} keywords out of a total {max_keywords}"

        # Check if the user has any keywords
        if not keyword_rows and not server_keyword_rows:
            return await ctx.send(f"You don't have any keywords. Set some up by running the `{ctx.prefix}addkeyword` command")
        
        # Set up a sendable list of keywords
        keyword_list = [row['keyword'] for row in keyword_rows]
        keywords_string = "`" + '`, `'.join(keyword_list) + "`"
        
        server_keyword_string = self.get_server_keywords(server_keyword_rows, True)

        # Make a message
        final_message = f"{total_keywords_message}\n\n__{user.mention}'s Keywords__\n{keywords_string}\n\n__{user.mention}'s Server Keywords__\n{server_keyword_string}"

        # Send it
        await ctx.send(final_message, allowed_mentions=discord.AllowedMentions.none())
    
    def get_server_keywords(self, keyword_rows, turn_to_string=False):
        # Creates a dict of server_id: keyword_list found in DB call
        keyword_dict = {}
        for row in keyword_rows:
            # Set up the server variables
            server_id = row['serverid']
            server = self.bot.get_guild(server_id)

            # Add the server keywords to the dict
            if server in keyword_dict.keys():
                keyword_dict[server].append(row['keyword'])
            else:
                keyword_dict[server] = [row['keyword']]
            
        if not turn_to_string:
            return keyword_dict
        
        # Turn the dict into a string
        sendable = ""
        for server, keyword_list in keyword_dict.items():
            # Add the server name to the string
            sendable += f"**{server.name}**\n"

            # Add the keywords to the string
            sendable += "`" + '`, `'.join(keyword_list) + "`" + "\n"
        
        return sendable

    @utils.command(aliases=['max', 'maxkey', 'maxwords', 'maxkeyword', 'maxkeys', 'maxword'])
    async def maxkeywords(self, ctx: utils.Context, user:discord.User=None):
        """Sends the maximum amount of keywords a user can have"""

        # Make sure we got a user
        user = user or ctx.author

        max_keywords = await self.get_max_keywords(user)

        await ctx.send(f"{user.mention} can set {max_keywords} keywords. Buy more at {self.bot.config['bot_info']['links']['Donate']['url']} :)", allowed_mentions=discord.AllowedMentions.none())


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

        if user.id in self.bot.owner_ids:
            keyword_max = 100

        return keyword_max


def setup(bot):
    bot.add_cog(BotCommands(bot))
