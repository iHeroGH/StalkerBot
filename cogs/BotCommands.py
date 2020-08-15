import discord
from discord.ext import commands
import asyncpg
import aiohttp
import json


class BotCommands(commands.Cog, name = "Bot Commands"):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def invite(self, ctx):
        """Sends an invite link for the bot"""

        bot_permissions = discord.Permissions(
            read_messages=True,
            send_messages=True
        )
        await ctx.send(f"<https://discord.com/api/oauth2/authorize?client_id=723813550136754216&permissions={bot_permissions.value}&scope=bot>")


    @commands.command()
    async def addkeyword(self, ctx, keyword):
        """Adds a keyword to your list of DM triggers"""

        # Checks if the keyword is too short
        if len(keyword) < 3:
            return await ctx.send("That keyword is too short. It must be at least 3 characters")

        keyword = keyword.lower()

        # Gets the specific userID (to make sure it doesn't already have the specified keyword)
        connection = await asyncpg.connect(**self.bot.database_auth)
        rows = await connection.fetch("select * from keywords where userid = $1 and keyword = $2;", ctx.author.id, keyword)

        # Checks if the user already has the keyword
        if len(rows) > 0:
            await ctx.send("You already have that as a keyword")
            await connection.close()
            return

        # Checks if the user has the maxiumum amount of keywords (5)
        rows = await connection.fetch("select * from keywords where userid = $1;", ctx.author.id)
        if len(rows) >= 5:
            await ctx.send("You already have the maximum amount of keywords (5)")
            await connection.close()
            return

        # Adds the keyword into the list
        else:
            await connection.fetch("insert into keywords VALUES($1, $2);", ctx.author.id, keyword)
        await connection.close()
        await ctx.send(f"Added `{keyword}` into <@{ctx.author.id}>'s list")


    @commands.command()
    async def removekeyword(self, ctx, keyword):
        """Removes a keyword from your list of DM triggers"""

        keyword = keyword.lower()

        # Gets the specific keyword and userID
        connection = await asyncpg.connect(**self.bot.database_auth)
        rows = await connection.fetch("select * from keywords where userid = $1 and keyword = $2;", ctx.author.id, keyword)

        # Checks if the row is already in the list
        if len(rows) == 0:
            await ctx.send("That wasn't an existing keyword")
            await connection.close()
            return

        # Deletes the keyword
        await connection.fetch("delete from keywords where userid = $1 and keyword = $2;", ctx.author.id, keyword)
        await connection.close()
        await ctx.send(f"Removed `{keyword}` from <@{ctx.author.id}>'s list")


    @commands.command()
    async def removeall(self, ctx):
        """Removes all keywords from your list of DM triggers"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("delete from keywords where userid = $1;", ctx.author.id)
        await connection.close()
        await ctx.send(f"Deleted all the keywords from <@{ctx.author.id}>'s list")


    @commands.command()
    async def listkeywords(self, ctx):
        """Lists all your keywords"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        rows = await connection.fetch("select * from keywords where userid = $1;", ctx.author.id)
        await connection.close()
        if len(rows) == 0:
            await ctx.send(f"You don't have any keywords. Set some up by running the `{ctx.prefix}addkeyword` command")
            return

        keywordList = []
        for row in rows:
            keywordList.append(row["keyword"])

        await ctx.send(', '.join(keywordList))


    @commands.command()
    async def suggest(self, ctx, *, suggestion=None):
        """
        Sends a suggestion message to the bot creator (@Hero#2313)
        """

        channel = self.bot.get_channel(739923715311140955)

        if suggestion is None:
            await ctx.send(f"You didn't suggest anything. `{ctx.prefix} suggestion (SUGGESTION)")
            return
        await channel.send(f"<@322542134546661388> New suggestion from <@{ctx.author.id}>: `{suggestion[:1975]}`")
        await ctx.send(f"Suggested `{suggestion[:1950]}`")


    @commands.Cog.listener()
    async def on_message(self, message):

        # Checks that it isn't a DM
        guild = message.guild
        if guild is None:
            return

        # Hard-coded user list
        # hero = guild.get_member(322542134546661388)
        megan = guild.get_member(413797321273245696)
        aiko = guild.get_member(590794167362388011)
        sapnap = guild.get_member(606044593624055820)
        channel = message.channel

        # Stalk people list
        userID = {
            141231597155385344: [aiko, megan, sapnap],
            539508943592882193: [aiko]
        }

        # Filter out bots
        if message.author.bot:
            return

        # Sends a message to a list of users whenever anyUser ID matches with the userID in the stalk people list :tm: list
        anyUser = userID.get(message.author.id, [])
        for user in anyUser:
            if user is None:
                continue
            if channel.permissions_for(user).read_messages:
                await user.send(f"<@!{message.author.id}> ({message.author.name}) has typed in <#{message.channel.id}>. They typed `{message.content[:1900]}` {(message.jump_url)}")

        # Connects to the DB
        connection = await asyncpg.connect(**self.bot.database_auth)
        keywordRows = await connection.fetch("SELECT * from keywords")
        settingRows = await connection.fetch("SELECT * from usersettings")
        await connection.close()

        settingDict = {}


        for row in settingRows:
            settingDict[row['userid']] = row

        # Gets the users and keywords for those users
        alreadySent = []
        for row in keywordRows:
            userID = row["userid"]
            keyword = row["keyword"]
            member = guild.get_member(userID)
            if member is None:
                continue

            # Checks if the user has already been sent a message
            if userID in alreadySent:
                continue
            
            # Checks if the author of the message is the member and checks if the member's settings allow for owntrigger
            try:
                if message.author == member and settingDict[member.id]['owntrigger'] is False:
                    continue
            except KeyError: 
                pass


            # Creates a list "lines" that splits the message content by new line. It then checks if the quote trigger setting is
            # turned on. If it isn't, it appends the item from the lines list to a list "nonQuoted". If the setting is enabled, it
            # just keeps nonQuoted as the original message. This prevents users from recieving the section of text that is quoted.
            lines = message.content.split('\n')
            nonQuoted = []
            try:
                if settingDict[member.id]['quotetrigger'] is False:
                    for i in lines:
                        if not i.startswith("> "):
                            nonQuoted.append(i)
                else:
                    nonQuoted = lines
            except KeyError:
                nonQuoted = lines
                pass
            content = '\n'.join(nonQuoted)

            # Sends a message to a user if their keyword is said
            if (keyword in content.lower()):
                if channel.permissions_for(member).read_messages:
                    await member.send(f"<@!{message.author.id}> ({message.author.name}) has typed the keyword (`{keyword}`) in <#{message.channel.id}>. They typed `{message.content[:1900]}` {(message.jump_url)}")
                    alreadySent.append(member.id)


    @commands.command()
    @commands.is_owner()
    async def listall(self, ctx, user: discord.User = None):
        """Lists either a user's entire list of keywords or the entire database"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        if user is not None:
            full = await connection.fetch("select * from keywords where userid = $1;", user.id)
        else:
            full = await connection.fetch("select * from keywords;")
        await connection.close()

        text = list()
        for x in full:
            user = self.bot.get_user(x['userid']) or await self.bot.fetch_user(x['userid'])
            text.append(f"User: {user.name}({user.id}) - Keyword: {x['keyword']}")
        text.sort()
        text = "\n".join(text)

        async with aiohttp.ClientSession() as session:
            async with session.post('https://hastebin.com/documents', data=text) as req:
                key = await req.json()

        await ctx.send(f"https://hastebin.com/raw/{key['key']}")


    @commands.command()
    @commands.is_owner()
    async def forceremove(self, ctx, user: discord.User, keyword):
        """Forcibly removes a keyword from a user"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("delete from keywords where userid = $1 and keyword = $2;", user.id, keyword)
        await connection.close()
        await ctx.send(f"Removed `{keyword}` from {user.name}'s list")


    @commands.command()
    @commands.is_owner()
    async def forceadd(self, ctx, user: discord.User, keyword):
        """Forcibly adds a keyword to a user"""

        connection = await asyncpg.connect(**self.bot.database_auth)
        await connection.fetch("insert into keywords VALUES($1, $2);", user.id, keyword)
        await connection.close()
        await ctx.send(f"Added `{keyword}` to {user.name}'s list")

    @commands.command()
    @commands.is_owner()
    async def countusers(self, ctx):
        """Counts how many unique user IDs there are""" 
        
        connection = await asyncpg.connect(**self.bot.database_auth)
        rows = await connection.fetch("SELECT DISTINCT userid FROM keywords;")
        await connection.close()
        
        await ctx.send(f"`{len(rows)}` users use your dumbass of a bot. How's it feel, bitch?")



def setup(bot):
    bot.add_cog(BotCommands(bot))
