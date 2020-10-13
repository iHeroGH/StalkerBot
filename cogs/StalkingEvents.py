import io
import random
import collections
import copy

import discord
from discord.ext import commands

class StalkingEvents(commands.Cog, name="Stalking Events (Message Send/Edit)"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        # Checks that it isn't a DM
        guild = message.guild
        if guild is None:
            return

        # Hard-coded user list
        try:
            hero = await guild.fetch_member(322542134546661388)
        except Exception:
            pass
        try:
            megan = await guild.fetch_member(413797321273245696)
        except Exception:
            pass
        try:
            aiko = await guild.fetch_member(590794167362388011)
        except Exception:
            pass
        try:
            sapnap = await guild.fetch_member(606044593624055820)
        except Exception:
            pass

        channel = message.channel

        # Stalk people list
        userID = {
            141231597155385344: [megan, sapnap],
            322542134546661388: [megan],
            413797321273245696: [hero, megan]
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
                sent_message = await user.send(f"<@!{message.author.id}> ({message.author.name}) has typed in <#{message.channel.id}>. They typed `{message.content[:1900]}` {(message.jump_url)}")
            if user == megan:
                await sent_message.add_reaction("\N{HEAVY BLACK HEART}")



        # Get everything (from the users who have had a keyword triggered) from the datbase
        async with self.bot.database() as db:
            keywordRows = await db("SELECT * from keywords WHERE $1 LIKE concat('%', keyword, '%')", message.content.lower())
            serverKeywordRows = await db("SELECT * from serverkeywords WHERE $1 LIKE concat('%', keyword, '%')", message.content.lower())
            muted = await db("SELECT * FROM tempmute WHERE time > timezone('utc',now())")
            mutedlist = [user['userid'] for user in muted]
            id_list = [row['userid'] for row in keywordRows + serverKeywordRows if row['userid'] not in mutedlist]
            settingRows = await db("SELECT * from usersettings WHERE userid=ANY($1::BIGINT[])", id_list)
            textFilters = await db("SELECT * FROM textfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            channelFilters = await db("SELECT * FROM channelfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            serverFilters = await db("SELECT * FROM serverfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            userFilters = await db("SELECT * FROM userfilters WHERE userid=ANY($1::BIGINT[])", id_list)


        # Split the database rows down into easily-worable dictionaries
        base_user_settings = {
            "keywords": [],
            "settings": {},
            "filters": {
                "textfilters": [],
                "channelfilters": [],
                "serverfilters": [],
                "userfilters": [],
            }
        }
        settingDict = collections.defaultdict(lambda: copy.deepcopy(base_user_settings))
        for row in settingRows:
            settingDict[row['userid']]['settings'] = dict(row)  # Just straight copy this row from the database
        for row in textFilters:
            settingDict[row['userid']]['filters']['textfilters'].append(row['textfilter'])  # Add the item to a list
        for row in channelFilters:
            settingDict[row['userid']]['filters']['channelfilters'].append(row['channelfilter'])  # Add the item to a list
        for row in serverFilters:
            settingDict[row['userid']]['filters']['serverfilters'].append(row['serverfilter'])  # Add the item to a list
        for row in userFilters:
            settingDict[row['userid']]['filters']['userfilters'].append(row['userfilter'])  # Add the item to a list


        # Non-Server Keywords
        # Gets the users and keywords for those users
        alreadySent = []
        for row in keywordRows + serverKeywordRows:
            if row['userid'] in mutedlist:
                continue
            userID = row["userid"]
            keyword = row["keyword"]
            try:
                member = guild.get_member(userID) or await guild.fetch_member(userID)
            except Exception as e:
                if message.guild.id == 649715200890765342:
                    print(e)
                continue
            if member is None:
                continue

            if row.get('serverid') is not None and message.guild.id != row['serverid']:
                continue

            # Checks if the user has already been sent a message
            if userID in alreadySent:
                continue

            # Checks if the author of the message is the member and checks if the member's settings allow for owntrigger
            if message.author == member and settingDict[member.id]['settings'].get('owntrigger', True) is False:
                continue

            # Creates a list "lines" that splits the message content by new line. It then checks if the quote trigger setting is
            # turned on. If it isn't, it appends the item from the lines list to a list "nonQuoted". If the setting is enabled, it
            # just keeps nonQuoted as the original message. This prevents users from recieving the section of text that is quoted.
            lines = message.content.split('\n')
            nonQuoted = []
            if settingDict[member.id]['settings'].get('quotetrigger', True) is False:
                for i in lines:
                    if not i.startswith("> "):
                        nonQuoted.append(i)
            else:
                nonQuoted = lines
            content = '\n'.join(nonQuoted)

            # Filters
            for i in settingDict[member.id]['filters']['serverfilters']:
                if i == message.guild.id:
                    content = None
            for i in settingDict[member.id]['filters']['channelfilters']:
                if i == message.channel.id:
                    content = None
            for i in settingDict[member.id]['filters']['userfilters']:
                if i == message.author.id:
                    content = None
            for i in settingDict[member.id]['filters']['textfilters']:
                if i.lower() in message.content.lower() and content is not None:
                    lowercaseI = i.lower()
                    lowerContent = content.lower()
                    content = lowerContent.replace(lowercaseI, "")

            # If there's no content to be examined, let's just skip the message
            if content is None or content.strip() == "":
                continue

            # See if we should send them a message
            if keyword not in content.lower():
                continue
            if channel.permissions_for(member).read_messages is False:
                continue

            # Sends a message to a user if their keyword is said
            if settingDict[member.id]['settings'].get('embedmessage', False):
                sendable_content = {'embed': self.create_message_embed(message, keyword)}
            else:
                if len(message.attachments) != 0:
                    url_list = [i.url for i in message.attachments]
                    lines = "Attatchment Links: "
                    for i in url_list:
                        lines = lines + f"\n<{i}>"
                    sendable_content = {'content': f"<@!{message.author.id}> ({message.author.name}) has typed the keyword (`{keyword}`) in <#{message.channel.id}>. They typed `{message.content[:1900]}` <{(message.jump_url)}>.\n{lines}"}
                else:
                    sendable_content = {'content': f"<@!{message.author.id}> ({message.author.name}) has typed the keyword (`{keyword}`) in <#{message.channel.id}>. They typed `{message.content[:1900]}` <{(message.jump_url)}>."}
            try:
                await member.send(**sendable_content)
            except discord.Forbidden:
                pass
            alreadySent.append(member.id)

    def create_message_embed(self, message:discord.Message, keyword:str=None) -> discord.Embed:
        """Creates a message embed that can be DMd to a user"""

        embed = discord.Embed()
        color = random.randint(0, 0xffffff)
        embed.color = color
        embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
        embed.title = "Message Content"
        embed.description = message.content
        embed.add_field(name="Message Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Message Link", value=f"[Click here]({message.jump_url})", inline=True)
        if len(message.attachments) != 0:
            url_list = [i.url for i in message.attachments]
            lines = ""
            for i in url_list:
                lines = lines + f"\n[Click Here]({i})"
            embed.add_field(name = "Attatchment Links", value= lines, inline = False)
        if keyword:
            embed.set_footer(text=f"Keyword: {keyword}")
        embed.timestamp = message.created_at
        return embed




    @commands.Cog.listener()
    async def on_message_edit(self, before, after):

        # Checks that it isn't a DM
        guild = after.guild
        if guild is None:
            return

        # Hard-coded user list

        try:
            hero = await guild.fetch_member(322542134546661388)
        except Exception:
            pass
        try:
            megan = await guild.fetch_member(413797321273245696)
        except Exception:
            pass
        try:
            aiko = await guild.fetch_member(590794167362388011)
        except Exception:
            pass
        try:
            sapnap = await guild.fetch_member(606044593624055820)
        except Exception:
            pass
        channel = after.channel

        # Stalk people list
        userID = {
            141231597155385344: [megan, sapnap],
            322542134546661388: [megan]
        }

        # Filter out bots
        if after.author.bot:
            return

        # Sends a message to a list of users whenever anyUser ID matches with the userID in the stalk people list :tm: list
        anyUser = userID.get(after.author.id, [])
        for user in anyUser:
            if user is None:
                continue
            if channel.permissions_for(user).read_messages:
                sent_message = await user.send(f"<@!{after.author.id}> ({after.author.name}) has edited a message in <#{after.channel.id}>. The edited message is `{after.content[:1900]}` {(after.jump_url)}")
            if user == megan:
                await sent_message.add_reaction("\N{HEAVY BLACK HEART}")



        # Get everything (from the users who have had a keyword triggered) from the datbase
        async with self.bot.database() as db:
            keywordRows = await db("SELECT * from keywords WHERE $1 LIKE concat('%', keyword, '%')", after.content.lower())
            serverKeywordRows = await db("SELECT * from serverkeywords WHERE $1 LIKE concat('%', keyword, '%')", after.content.lower())
            muted = await db("SELECT * FROM tempmute WHERE time > timezone('utc',now())")
            mutedlist = [user['userid'] for user in muted]
            id_list = [row['userid'] for row in keywordRows + serverKeywordRows if row['userid'] not in mutedlist]
            settingRows = await db("SELECT * from usersettings WHERE userid=ANY($1::BIGINT[])", id_list)
            textFilters = await db("SELECT * FROM textfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            channelFilters = await db("SELECT * FROM channelfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            serverFilters = await db("SELECT * FROM serverfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            userFilters = await db("SELECT * FROM userfilters WHERE userid=ANY($1::BIGINT[])", id_list)


        # Split the database rows down into easily-worable dictionaries
        base_user_settings = {
            "keywords": [],
            "settings": {},
            "filters": {
                "textfilters": [],
                "channelfilters": [],
                "serverfilters": [],
                "userfilters": [],
            }
        }
        settingDict = collections.defaultdict(lambda: copy.deepcopy(base_user_settings))
        for row in settingRows:
            settingDict[row['userid']]['settings'] = dict(row)  # Just straight copy this row from the database
        for row in textFilters:
            settingDict[row['userid']]['filters']['textfilters'].append(row['textfilter'])  # Add the item to a list
        for row in channelFilters:
            settingDict[row['userid']]['filters']['channelfilters'].append(row['channelfilter'])  # Add the item to a list
        for row in serverFilters:
            settingDict[row['userid']]['filters']['serverfilters'].append(row['serverfilter'])  # Add the item to a list
        for row in userFilters:
            settingDict[row['userid']]['filters']['userfilters'].append(row['userfilter'])  # Add the item to a list


        # Non-Server Keywords
        # Gets the users and keywords for those users
        alreadySent = []
        for row in keywordRows + serverKeywordRows:
            if row['userid'] in mutedlist:
                continue
            userID = row["userid"]
            keyword = row["keyword"]
            try:
                member = await guild.fetch_member(userID)
            except Exception:
                continue
            if member is None:
                continue

            if row.get('serverid') is not None and after.guild.id != row['serverid']:
                continue

            # Checks if the user has already been sent a message
            if userID in alreadySent:
                continue

            # Checks if the author of the message is the member and checks if the member's settings allow for owntrigger
            if after.author == member and settingDict[member.id]['settings'].get('owntrigger', True) is False:
                continue

            # Creates a list "lines" that splits the message content by new line. It then checks if the quote trigger setting is
            # turned on. If it isn't, it appends the item from the lines list to a list "nonQuoted". If the setting is enabled, it
            # just keeps nonQuoted as the original message. This prevents users from recieving the section of text that is quoted.
            lines = after.content.split('\n')
            nonQuoted = []
            if settingDict[member.id]['settings'].get('quotetrigger', True) is False:
                for i in lines:
                    if not i.startswith("> "):
                        nonQuoted.append(i)
            else:
                nonQuoted = lines
            content = '\n'.join(nonQuoted)

            # Filters
            for i in settingDict[member.id]['filters']['serverfilters']:
                if i == after.guild.id:
                    content = None
            for i in settingDict[member.id]['filters']['channelfilters']:
                if i == after.channel.id:
                    content = None
            for i in settingDict[member.id]['filters']['userfilters']:
                if i == after.author.id:
                    content = None
            for i in settingDict[member.id]['filters']['textfilters']:
                if i.lower() in after.content.lower() and content is not None:
                    lowercaseI = i.lower()
                    lowerContent = content.lower()
                    content = lowerContent.replace(lowercaseI, "")

            # If there's no content to be examined, let's just skip the message
            if content is None or content.strip() == "":
                continue

            # See if we should send them a message
            if keyword not in content.lower():
                continue
            if channel.permissions_for(member).read_messages is False:
                continue

            # Sends a message to a user if their keyword is said
            if settingDict[member.id]['settings'].get('embedmessage', False):
                sendable_content = {'embed': self.create_edit_message_embed(before, after, keyword)}
            else:
                if len(after.attachments) != 0:
                    url_list = [i.url for i in after.attachments]
                    lines = "Attatchment Links: "
                    for i in url_list:
                        lines = lines + f"\n<{i}>"
                    sendable_content = {'content': f"<@!{after.author.id}> ({after.author.name}) has edited a message to include your keyword (`{keyword}`) in <#{after.channel.id}>. They typed `{after.content[:1900]}` <{(after.jump_url)}>.\n{lines}"}
                else:
                    sendable_content = {'content': f"<@!{after.author.id}> ({after.author.name}) has edited a message to include your keyword (`{keyword}`) in <#{after.channel.id}>. They typed `{after.content[:1900]}` <{(after.jump_url)}>."}
            try:
                await member.send(**sendable_content)
            except discord.Forbidden:
                pass
            alreadySent.append(member.id)

    def create_edit_message_embed(self, before:discord.Message, after:discord.Message, keyword:str=None) -> discord.Embed:
        """Creates a message embed that can be DMd to a user"""

        embed = discord.Embed()
        color = random.randint(0, 0xffffff)
        embed.color = color
        embed.set_author(name=str(after.author), icon_url=after.author.avatar_url)
        embed.title = "Before Message Content"
        embed.description = before.content
        embed.add_field(name="After Message Content", value = after.content, inline=False)
        embed.add_field(name="Message Channel", value=after.channel.mention, inline=True)
        embed.add_field(name="Message Link", value=f"[Click here]({after.jump_url})", inline=True)
        if len(after.attachments) != 0:
            url_list = [i.url for i in after.attachments]
            lines = ""
            for i in url_list:
                lines = lines + f"\n[Click Here]({i})"
            embed.add_field(name = "Attatchment Links", value= lines, inline = False)
        if keyword:
            embed.set_footer(text=f"Keyword: {keyword}")
        embed.timestamp = after.created_at
        return embed




def setup(bot):
    bot.add_cog(StalkingEvents(bot))
