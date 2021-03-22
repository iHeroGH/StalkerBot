import io
from datetime import datetime as dt, timedelta

import discord
from discord.ext import commands
import voxelbotutils as utils


class BotCommands(utils.Cog, name="Bot Commands"):

    MAXIMUM_ALLOWED_KEYWORDS = 10
    MINIMUM_KEYWORD_LENGTH = 2

    @utils.command()
    async def info(self, ctx):
        """Explains the bot"""

        with utils.Embed(use_random_colour=True) as embed:
            stalker = self.bot.get_user(723813550136754216) or await self.bot.fetch_user(723813550136754216)
            embed.set_author(name=str(stalker), icon_url=stalker.avatar_url)
            embed.description = "StalkerBot is just a simple bot that sends you a DM every time a keyword that you set is said in a channel you have access to!\nYour keywords are *global*, but you can set *server-specific keywords* aswell.\nFinally, you can add *filters* for certain users, text phrases, channels, and even servers. These filters prevent you from getting DMed about your keyword if it's said by a specific user, in a specific text phrase, in a specific channel, or in a specific server.\nRun `s.help` for more."
            embed.set_image(url="https://cdn.discordapp.com/attachments/723820365612187690/753286003283722330/unknown.png")
            embed.set_thumbnail(url=stalker.avatar_url)

        await ctx.send(embed=embed)

    @utils.command(aliases=['tm', 'mute'])
    async def tempmute(self, ctx, time:int, unit:str="m"):
        """Temporarily mutes the bot from sending a user DMs for a specificed amount of time"""
        unit = unit.lower()

        # Checks that units are valid
        valid_units = {
            "s": 1,
            "m": 60,
            "h": 60 * 60,
            "d": 60 * 60 * 24,
        }

        if unit not in valid_units.keys():
            return await ctx.send("You didn't provide a valid unit (s, m, h, d)")

        # Checks that time is above 0
        if time <= 0:
            return await ctx.send("The time value you provided is under 0 seconds")

        # Change all time into seconds
        seconded_time = valid_units[unit] * time

        # Add time
        future = dt.utcnow() + timedelta(seconds=seconded_time)

        # Add to database
        async with self.bot.database() as db:
            await db("INSERT INTO tempmute VALUES($1, $2) ON CONFLICT (userid) DO UPDATE SET time = $2;", ctx.author.id, future)

        await ctx.send(f"I won't send you messages for the next `{time}{unit}`")

    @utils.command(aliases=['unm', "um"])
    async def unmute(self, ctx):
        """Unmutes StalkerBot from sending a user messages"""

        # Remove the user from the tempmute database
        async with self.bot.database() as db:
            await db("DELETE FROM tempmute WHERE userid=$1;", ctx.author.id)

        await ctx.send("Unmuted StalkerBot.")

    @utils.command(aliases=['keyword', 'add'])
    async def addkeyword(self, ctx, *, keyword:str):
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
    async def addserverkeyword(self, ctx, serverid:int, *, keyword:str):
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
    async def removekeyword(self, ctx, *, keyword:str):
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
    async def removeserverkeyword(self, ctx, serverid:int, *, keyword:str):
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

        # If the author isn't the owner of the bot, list the author's keywords
        if not (await self.bot.is_owner(ctx.author)):
            user = ctx.author

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

    @utils.command(aliases=['serverkeywords', 'serverkeywordlist', 'serverkeywordslist', 'serverlist'])
    async def listserverkeywords(self, ctx):
        """Lists all your server-specific keywords"""

        async with self.bot.database() as db:
            rows = await db("SELECT * FROM serverkeywords WHERE userid = $1;", ctx.author.id)
        if len(rows) == 0:
            await ctx.send(f"You don't have any server-specific keywords. Set some up by running the `{ctx.prefix}addkeyword` command")
            return

        # Creates a list of server:keywords found in DB call
        keywordList = []
        for row in rows:
            keywordList.append(f"`Server: {self.bot.get_guild(row['serverid']).name} ({row['serverid']})` , Keyword: `{row['keyword']}`")
            keywordList.sort()

        sendableContent = "Server-Specific Keywords: "
        for i in keywordList:
            sendableContent = sendableContent + f"\n{str(i)}"

        await ctx.send(sendableContent, allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @utils.command()
    async def suggest(self, ctx, *, suggestion:str=None):
        """Sends a suggestion message to the bot creator (@Hero#2313)"""

        channel = self.bot.get_channel(739923715311140955)

        if suggestion is None:
            await ctx.send_help(ctx.command)
            return
        await channel.send(f"<@322542134546661388> New suggestion from <@{ctx.author.id}> (`{ctx.author.id}`): `{suggestion[:1950]}`")
        await ctx.send(f"Suggested `{suggestion[:1950]}`", )

    @utils.command()
    @commands.is_owner()
    async def listall(self, ctx, user:discord.User=None):
        """Lists either a user's entire list of keywords or the entire database"""

        async with self.bot.database() as db:
            if user is not None:
                full = await db("SELECT * FROM keywords WHERE userid = $1;", user.id)
            else:
                full = await db("SELECT * FROM keywords;")

        text = list()
        for x in full:
            user = self.bot.get_user(x['userid']) or await self.bot.fetch_user(x['userid'])
            text.append(f"User: {user.name}({user.id}) - Keyword: {x['keyword']}")
        text = "\n".join(sorted(text)) + "\n"
        await ctx.send(file=discord.File(io.StringIO(text), filename="AllUsers.txt"))

    @utils.command()
    @commands.is_owner()
    async def forceremove(self, ctx, user:discord.User, keyword:str):
        """Forcibly removes a keyword from a user"""

        async with self.bot.database() as db:
            await db("DELETE FROM keywords WHERE userid = $1 AND keyword = $2;", user.id, keyword)

        await ctx.send(f"Removed `{keyword}` from {user.name}'s list")

    @utils.command()
    @commands.is_owner()
    async def forceadd(self, ctx, user:discord.User, keyword:str):
        """Forcibly adds a keyword to a user"""

        async with self.bot.database() as db:
            await db("INSERT INTO keywords VALUES ($1, $2);", user.id, keyword)
        await ctx.send(f"Added `{keyword}` to {user.name}'s list")

    async def get_max_keywords(self, user:discord.User):
        """Returns the max. amount of keywords a user can have based on upgrade.chat"""

        orders = await self.bot.upgrade_chat.get_orders(discord_id=user.id)

        for p in orders:
            for i in p.order_items:
                if i.product_name != "5x StalkerBot Keywords":
                    continue
                total_purchases += i.quantity

        keyword_max = self.MAXIMUM_ALLOWED_KEYWORDS + (len(total_purchases) * 5)
        return keyword_max


def setup(bot):
    bot.remove_command("info")
    bot.add_cog(BotCommands(bot))
