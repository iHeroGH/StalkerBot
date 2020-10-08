import random
import collections
import copy
import re
import typing

import discord
from discord.ext import commands


class StalkingEvents(commands.Cog, name="Stalking Events (Message Send/Edit)"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        await self.deal_with_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):

        await self.deal_with_message(after, edited_message=before)

    async def deal_with_message(self, message, edited_message=None):

        # Checks that it isn't a DM
        guild = message.guild
        if guild is None:
            return

        # Hard-coded user list
        megan = self.bot.get_user(413797321273245696)
        sapnap = self.bot.get_user(606044593624055820)
        channel = message.channel

        # Stalk people list
        user_id = {
            141231597155385344: [megan, sapnap],
            322542134546661388: [megan]
        }

        # Filter out bots
        if message.author.bot:
            return

        # Sends a message to a list of users whenever anyUser ID matches with the user_id in the stalk people list :tm: list
        anyUser = user_id.get(message.author.id, [])
        for user in anyUser:
            if user is None:
                continue
            if channel.permissions_for(user).read_messages:
                sent_message = await user.send(f"<@!{message.author.id}> ({message.author.name}) has typed in <#{message.channel.id}>. They typed `{message.content[:1900]}` {(message.jump_url)}")
            if user == megan:
                heart_codepoints = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤎", "🤍"]
                await sent_message.add_reaction(random.choice(heart_codepoints))

        # Get everything (from the users who have had a keyword triggered) from the datbase
        async with self.bot.database() as db:
            # Grab users whose keywords have been triggered
            keyword_rows = await db("SELECT * from keywords WHERE $1 LIKE concat('%', keyword, '%')", message.content.lower())
            server_keyword_rows = await db("SELECT * from serverkeywords WHERE $1 LIKE concat('%', keyword, '%')", message.content.lower())

            # Filter out those who have the bot muted
            muted = await db("SELECT * FROM tempmute WHERE time > timezone('utc',now())")
            mutedlist = [user['userid'] for user in muted]

            # Make a list of people who we might actually DM so we can only grab THEIR settings from the database
            id_list = [row['userid'] for row in keyword_rows + server_keyword_rows if row['userid'] not in mutedlist]
            setting_rows = await db("SELECT * from usersettings WHERE userid=ANY($1::BIGINT[])", id_list)
            text_filters = await db("SELECT * FROM textfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            channel_filters = await db("SELECT * FROM channelfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            server_filters = await db("SELECT * FROM serverfilters WHERE userid=ANY($1::BIGINT[])", id_list)
            user_filters = await db("SELECT * FROM userfilters WHERE userid=ANY($1::BIGINT[])", id_list)

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
        settings_dict = collections.defaultdict(lambda: copy.deepcopy(base_user_settings))
        for row in setting_rows:
            settings_dict[row['userid']]['settings'] = dict(row)  # Just straight copy this row from the database
        for row in text_filters:
            settings_dict[row['userid']]['filters']['textfilters'].append(row['textfilter'])  # Add the item to a list
        for row in channel_filters:
            settings_dict[row['userid']]['filters']['channelfilters'].append(row['channelfilter'])  # Add the item to a list
        for row in server_filters:
            settings_dict[row['userid']]['filters']['serverfilters'].append(row['serverfilter'])  # Add the item to a list
        for row in user_filters:
            settings_dict[row['userid']]['filters']['userfilters'].append(row['userfilter'])  # Add the item to a list

        # Go through the settings for the users and see if we should bother messaging them
        already_sent = []  # Users who were already sent a DM
        for row in keyword_rows + server_keyword_rows:

            # Expand out our vars
            user_id = row["userid"]
            keyword = row["keyword"]

            # Only DM the user if we haven't send them anything already
            if user_id in already_sent:
                continue

            # Only DM the user if they've not muted the bot
            if user_id in mutedlist:
                continue

            # Only DM the user if they're in the server where the keyword was triggered
            member = guild.get_member(user_id)
            if member is None:
                continue

            # If the keyword is only for a certain guild and it ISNT this one, continue
            if row.get('serverid') is not None and message.guild.id != row['serverid']:
                continue

            # Checks if the author of the message is the member and checks if the member's settings allow for owntrigger
            if message.author == member and settings_dict[member.id]['settings'].get('owntrigger', True) is False:
                continue

            # Filter out quoted text if the user doesn't want any
            content = message.content
            if settings_dict[member.id]['settings'].get('quotetrigger', True) is False:
                lines = message.content.split('\n')
                nonQuoted = []
                for i in lines:
                    if not i.startswith("> "):
                        nonQuoted.append(i)
                content = '\n'.join(nonQuoted)

            # Deal with filters
            for guild_id in settings_dict[member.id]['filters']['serverfilters']:
                if guild_id == message.guild.id:
                    content = None
            for channel_id in settings_dict[member.id]['filters']['channelfilters']:
                if channel_id == message.channel.id:
                    content = None
            for user_id in settings_dict[member.id]['filters']['userfilters']:
                if user_id == message.author.id:
                    content = None
            for keyword in settings_dict[member.id]['filters']['textfilters']:
                if keyword.lower() in message.content.lower() and content is not None:
                    content = re.sub(re.escape(keyword), "", content)

            # If there's no content to be examined, let's just skip the message
            if content is None or content.strip() == "":
                continue

            # See if we should send them a message
            if keyword not in content.lower():
                continue
            if channel.permissions_for(member).read_messages is False:
                continue

            # Generate the content to be sent to the user
            if settings_dict[member.id]['settings'].get('embedmessage', False):
                if edited_message:
                    sendable_content = {'embed': self.create_message_embed((edited_message, message,), keyword)}
                else:
                    sendable_content = {'embed': self.create_message_embed(message, keyword)}
            else:
                if edited_message:
                    sendable_content = {'content': self.create_message_string(message, keyword, edited=True)}
                else:
                    sendable_content = {'content': self.create_message_string(message, keyword)}

            # Try and send it to them
            try:
                await member.send(**sendable_content)
            except discord.HTTPException:
                pass
            already_sent.append(member.id)

    def create_message_embed(self, message:typing.Union[discord.Message, typing.Tuple[discord.Message]], keyword:str=None) -> discord.Embed:
        """Creates a message embed that can be DMd to a user"""

        try:
            before, message = message
        except TypeError:
            before, message = None, message

        embed = discord.Embed()
        color = random.randint(0, 0xffffff)
        embed.color = color
        embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
        if before:
            embed.add_field(name="Before Message Content", value=before.content, inline=False)
            embed.add_field(name="After Message Content", value=message.content, inline=False)
        else:
            embed.add_field(name="Message Content", value=message.content, inline=False)
        embed.add_field(name="Message Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Message Link", value=f"[Click here]({message.jump_url})", inline=True)
        if len(message.attachments) != 0:
            url_list = [i.url for i in message.attachments]
            lines = ""
            for i in url_list:
                lines = lines + f"\n[Click Here]({i})"
            embed.add_field(name="Attatchment Links", value=lines, inline=False)
        if keyword:
            embed.set_footer(text=f"Keyword: {keyword}")
        embed.timestamp = message.created_at
        return embed

    def create_message_string(self, message:discord.Message, keyword:str, *, edited:bool=False) -> str:
        """Creates a string that can be DMd to a user"""

        message = message

        if edited:
            lines = [f"<@!{message.author.id}> ({message.author.name}) has been edited to include the keyword (`{keyword}`) in <#{message.channel.id}>. They typed `{message.content[:1900]}` <{(message.jump_url)}>."]
        else:
            lines = [f"<@!{message.author.id}> ({message.author.name}) has typed the keyword (`{keyword}`) in <#{message.channel.id}>. They typed `{message.content[:1900]}` <{(message.jump_url)}>."]
        if len(message.attachments) != 0:
            lines.append("Attachment Links:")
            url_list = [i.url for i in message.attachments]
            for i in url_list:
                lines.append(f"\n<{i}>")
        return '\n'.join(lines)


def setup(bot):
    bot.add_cog(StalkingEvents(bot))
