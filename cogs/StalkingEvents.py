import collections
import copy
import re
import typing

import discord
import voxelbotutils as utils


class StalkingEvents(utils.Cog, name="Stalking Events (Message Send/Edit)"):

    STALKER_CHANNEL = 772615385102549022

    @utils.Cog.listener()
    async def on_message(self, message):

        await self.deal_with_message(message)

    @utils.Cog.listener()
    async def on_message_edit(self, before, after):

        # Checks if the message content has changed
        if(before.content == after.content):
            return

        await self.deal_with_message(after, edited_message=before)

    async def deal_with_message(self, message, edited_message=None):

        # Only run if the bot is ready
        if not self.bot.is_ready():
            return

        # Checks that it isn't a DM (and send a message to the stalking channel if the message sent to the bot doesn't start with the prefix)
        guild = message.guild
        if guild is None:
            if not message.content.lower().startswith("s.") and message.author.id != 723813550136754216:  # Stalker's ID
                embed = discord.Embed()
                embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
                embed.set_footer(text=f"Author: {str(message.author)} ({message.author.id})\nChannel ID: {message.channel.id}\nMessage ID: {message.id}")
                if message.attachments:
                    url_list = [i.url for i in message.attachments]
                    lines = ""
                    for i in url_list:
                        lines = lines + f"\n[Click Here]({i})"
                    embed.add_field(name="Attatchment Links", value=lines, inline=False)
                    embed.set_image(url=message.attachments[0].url)
                embed.description = message.content
                return await self.bot.get_channel(self.STALKER_CHANNEL).send(embed=embed)
            return
        channel = message.channel

        # Filter out StalkerBot
        if message.author == message.guild.me:
            return

        # React with eyes if message contains "Stalker" lol (only on Voxel Fox)
        if guild.id == 208895639164026880:
            if "stalker" in message.content.lower():
                await message.add_reaction("👀")
            if "reklats" in message.content.lower():
                await message.add_reaction("<:backwards_eyes:785981504127107112>")

        # # Send a message to a channel on the StalkerBot test server if "stalkerbot" or the bot's id is in the message
        # if "stalkerbot" in message.content.lower() or f"{message.guild.me.id}" in message.content.lower():
        #     embed = discord.Embed()
        #     embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
        #     embed.set_footer(text=f"Author: {str(message.author)} ({message.author.id})\nChannel: {message.channel.name} ({message.channel.id})\nGuild: {message.guild.name} ({message.guild.id})")
        #     embed.description = message.content
        #     await self.bot.get_channel(self.STALKER_CHANNEL).send(embed=embed)

        # # Stalk people list
        # all_message_stalks = {}  #{'megan': 413797321273245696, 'sapnap': 606044593624055820, 'hero': 322542134546661388}
        # user_id = {
        #     141231597155385344: ['megan', 'sapnap'],
        #     322542134546661388: ['megan'],
        # }

        # # Sends a message to a list of users whenever user_dm_list ID matches with the user_id in the stalk people list :tm: list
        # user_dm_list = user_id.get(message.author.id, [])
        # for user_name in user_dm_list:

        #     # Try and grab the member object
        #     self.bot.logger.debug(f"Trying to send message {message.id} by {message.author.id} to '{user_name}'")
        #     try:
        #         user_id = all_message_stalks.get(user_name)
        #         assert user_id is not None
        #         user = guild.get_member(user_id) or await guild.fetch_member(user_id)
        #     except (AssertionError, discord.HTTPException):
        #         continue
        #     if user is None:
        #         continue

        #     # Make sure they can read messages
        #     if not channel.permissions_for(user).read_messages:
        #         continue

        #     # Send message
        #     self.bot.logger.info(f"Sending message {message.id} by {message.author.id} to {user.id} as part of all message stalking")
        #     try:
        #         sent_message = await user.send(f"<@!{message.author.id}> ({message.author.name}) has typed in <#{message.channel.id}>. They typed `{message.content[:1900]}` {(message.jump_url)}")
        #     except discord.HTTPException:
        #         continue

        #     # We love Megan <3
        #     if user_name == 'megan':
        #         heart_codepoints = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤎", "🤍"]
        #         #await sent_message.add_reaction(random.choice(heart_codepoints))

        # Get everything (from the users who have had a keyword triggered) from the datbase
        async with self.bot.database() as db:

            # Grab users whose keywords have been triggered
            keyword_rows = await db("SELECT * from keywords WHERE $1 LIKE concat('%', keyword, '%')", message.content.lower())
            server_keyword_rows = await db("SELECT * from serverkeywords WHERE $1 LIKE concat('%', keyword, '%')", message.content.lower())

            # Filter out those who have the bot muted
            muted = await db("SELECT * FROM tempmute WHERE time > TIMEZONE('UTC', NOW())")
            mutedlist = [user['userid'] for user in muted]

            # Make a list of people who we might actually DM so we can only grab THEIR settings from the database
            id_list = [row['userid'] for row in keyword_rows + server_keyword_rows if row['userid'] not in mutedlist]
            setting_rows = await db("SELECT * from user_settings WHERE user_id=ANY($1::BIGINT[])", id_list)
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
            settings_dict[row['user_id']]['settings'] = dict(row)  # Just straight copy this row from the database
        for row in text_filters:
            settings_dict[row['userid']]['filters']['textfilters'].append(row['textfilter'])  # Add the item to a list
        for row in channel_filters:
            settings_dict[row['userid']]['filters']['channelfilters'].append(row['channelfilter'])  # Add the item to a list
        for row in server_filters:
            settings_dict[row['userid']]['filters']['serverfilters'].append(row['serverfilter'])  # Add the item to a list
        for row in user_filters:
            settings_dict[row['userid']]['filters']['userfilters'].append(row['userfilter'])  # Add the item to a list

        # members_in_guild = {i.id: i for i in await message.guild.query_members(user_ids=id_list)}

        # Go through the settings for the users and see if we should bother messaging them
        already_sent = set()  # Users who were already sent a DM
        for row in keyword_rows + server_keyword_rows:

            # Expand out our vars
            user_id = row["userid"]
            keyword = row["keyword"]

            # Only DM the user if they've not muted the bot
            if user_id in mutedlist:
                continue

            # Don't DM the user if we already sent them something
            if user_id in already_sent:
                continue

            # Grab the member object
            self.bot.logger.debug(f"Grabbing member {user_id} in guild {guild.id}")
            try:
                member = guild.get_member(user_id) or await guild.fetch_member(user_id)
                assert member is not None
            except (AssertionError, discord.HTTPException):
                self.bot.logger.debug(f"Member {user_id} in guild {guild.id} doesn't exist :/")
                continue

            # Filter out bots
            if settings_dict[member.id]['settings'].get('bottrigger', True) is False:
                if message.author.bot:
                    return

            # If the keyword is only for a certain guild and it ISN'T this one, continue
            if row.get('serverid') is not None and message.guild.id != row['serverid']:
                self.bot.logger.debug(f"Not sending message to {user_id} because of guild specific keyword")
                continue

            # Checks if the author of the message is the member and checks if the member's settings allow for owntrigger
            if message.author == member and settings_dict[member.id]['settings'].get('owntrigger', True) is False:
                self.bot.logger.debug(f"Not sending message to {user_id} because of owntrigger")
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
                    self.bot.logger.debug(f"Not sending message to {user_id} because of server filter")
                    content = None
            for channel_id in settings_dict[member.id]['filters']['channelfilters']:
                if channel_id == message.channel.id:
                    self.bot.logger.debug(f"Not sending message to {user_id} because of channel filter")
                    content = None
            for user_id in settings_dict[member.id]['filters']['userfilters']:
                if user_id == message.author.id:
                    self.bot.logger.debug(f"Not sending message to {user_id} because of user filter")
                    content = None
            for kw in settings_dict[member.id]['filters']['textfilters']:
                if kw.lower() in message.content.lower() and content is not None:
                    content = re.sub(re.escape(kw.lower()), "", content.lower())

            # If there's no content to be examined, let's just skip the message
            if content is None or content.strip() == "":
                self.bot.logger.debug(f"Not sending message to {user_id} because of text filter")
                continue

            # See if we should send them a message
            if keyword.lower() not in content.lower():
                self.bot.logger.debug(f"Not sending message to {user_id} because of text filter")
                continue
            if channel.permissions_for(member).read_messages is False:
                self.bot.logger.debug(f"Not sending message to {user_id} because of missing permissions")
                continue

            # Checks if the message is edited and if the user wants edited messages
            if edited_message and settings_dict[member.id]['settings'].get('editmessage', True) is False:
                self.bot.logger.debug(f"Not sending message to {user_id} because of editmessage")
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
            self.bot.logger.info(f"Sending message {message.id} by {message.author.id} to {member.id} for keyword trigger")
            try:
                await member.send(**sendable_content)
            except discord.HTTPException:
                pass
            already_sent.add(member.id)

    def create_message_embed(self, message:typing.Union[discord.Message, typing.Tuple[discord.Message]], keyword:str=None) -> discord.Embed:
        """Creates a message embed that can be DMd to a user"""

        try:
            before, message = message
        except TypeError:
            before, message = None, message

        embed = discord.Embed()
        color = abs(hash(keyword)) & 0xffffff  #random.randint(0, 0xffffff)
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
            lines = [f"<@!{message.author.id}> ({message.author.name}) has edited their message to include the keyword (`{keyword}`) in <#{message.channel.id}>. They typed `{message.content[:1900]}` <{(message.jump_url)}>."]
        else:
            lines = [f"<@!{message.author.id}> ({message.author.name}) has typed the keyword (`{keyword}`) in <#{message.channel.id}>. They typed `{message.content[:1900]}` <{(message.jump_url)}>."]
        if len(message.attachments) != 0:
            lines.append("Attachment Links:")
            url_list = [i.url for i in message.attachments]
            for i in url_list:
                lines.append(f"\n<{i}>")
        return '\n'.join(lines)

    def message_is_embed(self, message:discord.Message):
        """Does things if a message is an embed"""

        if len(message.embeds) < 0:
            return

        embed_value_list = []
        for i in message.embeds:
            embed_values = {
                'Title': i.title,
                'Desc': i.description,
                'Fields': [{j.name: j.value} for j in i.fields],
                'Author': i.author.name,
                'Footer': i.footer.text
            }
            embed_value_list.append(embed_values)

        return embed_value_list


def setup(bot):
    bot.add_cog(StalkingEvents(bot))
