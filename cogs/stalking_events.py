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

        # Check if the message's embeds changed
        if before.embeds and after.embeds:
            if len(before.embeds) == len(after.embeds):
                if before.embeds[0].to_dict() == after.embeds[0].to_dict():
                    return
        # Checks if the message content has changed
        elif before.content == after.content:
            return

        await self.deal_with_message(after, edited_message=before)

    async def message_is_embed(self, message:discord.Message):
        """Scan embedded messages for keywords"""

        if not message.embeds:
            return

        for embed in message.embeds:
            embed_dict = embed.to_dict()
            embed_str = self.get_dict_string(embed_dict)
            await self.deal_with_message(message, embed_content=embed_str)

    async def deal_with_message(self, message:discord.Message, embed_content=None, edited_message=None):

        # Only run if the bot is ready
        if not self.bot.is_ready():
            return

        # If we're in a guild
        if message.guild is None:
            return

        guild = message.guild
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

        # Check if we're scanning for an embed
        if not embed_content and message.embeds:
            self.bot.logger.info(f"Embed message found {message.id}")
            return await self.message_is_embed(message)

        already_sent = set()  # Users who were already sent a DM

        # Deal with the reply message stuff
        reference = message.reference
        if reference:
            async with self.bot.database() as db:
                reply_on_rows = await db("SELECT * from user_settings WHERE replymessage=true")

            # Create a list of all the user IDs of the people who have reply_rows turned on
            reply_users = {i['user_id']: (i['embedmessage'], i['owntrigger']) for i in reply_on_rows}

            # Get the message
            reply_message = None
            for i in self.bot.cached_messages:
                if i.id == reference.message_id:
                    reply_message = i
                    self.bot.logger.info(f"Found reply message {reply_message.id} in cache")
                    break
            if reply_message is None:
                reply_message = await message.channel.fetch_message(reference.message_id)
                self.bot.logger.info(f"Fetched reply message {reply_message.id} from API")

            # Send a DM to the author
            if reply_message.author.id in reply_users:
                if reply_message.author.id == message.author.id:
                    if not reply_users[reply_message.author.id][1]:
                        self.bot.logger.info(f"Message reply {reply_message.id} triggered a reply message, but was blocked by owntrigger")
                        return
                if reply_users[reply_message.author.id][0]:
                    sendable_content = {'embed': self.create_message_embed(message, reply=True)}
                else:
                    sendable_content = {'content': self.create_message_string(message, None, False, True)}
                self.bot.logger.info(f"Sending message {message.id} by {message.author.id} to {reply_message.author.id} for reply trigger")
                self.bot.loop.create_task(reply_message.author.send(**sendable_content, embeddify= (False if "content" in sendable_content else True)))
                already_sent.add(reply_message.author.id)
            else:
                self.bot.logger.info(f"Message reply {reply_message.id} didn't trigger a replymessage")

        scanned_content = embed_content or message.content

        # Get everything (from the users who have had a keyword triggered) from the datbase
        async with self.bot.database() as db:

            # Grab users whose keywords have been triggered
            keyword_rows = await db("SELECT * from keywords WHERE $1 LIKE concat('%', keyword, '%')", scanned_content.lower())
            server_keyword_rows = await db("SELECT * from serverkeywords WHERE $1 LIKE concat('%', keyword, '%')", scanned_content.lower())

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
                member = guild.get_member(user_id)  # or await guild.fetch_member(user_id)
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
            content = embed_content or message.content
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
                if kw.lower() in (embed_content or message.content).lower() and content is not None:
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
                if embed_content:
                    sendable_content = {'embed': self.create_message_embed(message, keyword, embed_content)}
                elif edited_message:
                    sendable_content = {'embed': self.create_message_embed((edited_message, message,), keyword)}
                else:
                    sendable_content = {'embed': self.create_message_embed(message, keyword)}
            else:
                if embed_content:
                    sendable_content = {'content': self.create_message_string(message, keyword, embed_content)}
                elif edited_message:
                    sendable_content = {'content': self.create_message_string(message, keyword, edited=True)}
                else:
                    sendable_content = {'content': self.create_message_string(message, keyword)}

            # Try and send it to them
            self.bot.logger.info(f"Sending message {message.id} by {message.author.id} to {member.id} for keyword trigger")

            self.bot.logger.info(f"Adding {member.id} to already_sent")
            already_sent.add(member.id)

            self.bot.loop.create_task(member.send(**sendable_content, embeddify= (False if "content" in sendable_content else True))) # Finally send the message. Turn off embeddify if it's just content

    def create_message_embed(self, message:typing.Union[discord.Message, typing.Tuple[discord.Message]], keyword:str=None, embed_content:str=None, reply:bool=False) -> discord.Embed:
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
            embed.add_field(name="Message Content", value=f"Keyword was found in an embed: {embed_content}" if embed_content else message.content, inline=False)
        embed.add_field(name="Message Channel", value=f"{message.channel.mention}\n({message.guild.name}: {message.channel.name})", inline=True)
        embed.add_field(name="Message Link", value=f"[Click here]({message.jump_url})", inline=True)
        if len(message.attachments) != 0:
            url_list = [i.url for i in message.attachments]
            lines = ""
            for i in url_list:
                lines = lines + f"\n[Click Here]({i})"
            embed.add_field(name="Attatchment Links", value=lines, inline=False)
        if keyword:
            embed.set_footer(text=f"Keyword: {keyword}")
        if reply:
            embed.set_footer(text=f"Reply")
        embed.timestamp = message.created_at
        return embed

    def create_message_string(self, message:discord.Message, keyword:str=None, embed_content:str=None, edited:bool=False, reply:bool=False) -> str:
        """Creates a string that can be DMd to a user"""

        message = message

        if reply:
            lines = [f"<@!{message.author.id}> ({message.author.name}) has replied to your message in {message.channel.mention} ({message.guild.name}: {message.channel.name}). They typed `{message.content[:1900]}` <{(message.jump_url)}>."]
        elif edited:
            lines = [f"<@!{message.author.id}> ({message.author.name}) has edited their message to include the keyword (`{keyword}`) in {message.channel.mention} ({message.guild.name}: {message.channel.name}). They typed `{message.content[:1900]}` <{(message.jump_url)}>."]
        elif embed_content:
            lines = [f"<@!{message.author.id}> ({message.author.name}) has sent an embedded message containing the keyword (`{keyword}`) in {message.channel.mention} ({message.guild.name}: {message.channel.name}). The embed content was `{embed_content[:1900]}` <{(message.jump_url)}>."]
        else:
            lines = [f"<@!{message.author.id}> ({message.author.name}) has typed the keyword (`{keyword}`) in {message.channel.mention} ({message.guild.name}: {message.channel.name}). They typed `{message.content[:1900]}` <{(message.jump_url)}>."]
        if len(message.attachments) != 0:
            lines.append("Attachment Links:")
            url_list = [i.url for i in message.attachments]
            for i in url_list:
                lines.append(f"\n<{i}>")
        return '\n'.join(lines)

    def get_dict_string(self, embed_dict:dict):
        """Get all the strings from an embed"""
        strings = []
        # Embed Author
        if (author := embed_dict.get("author")):
            strings.append(author['name'])
            if (author_icon := embed_dict.get("icon_url")):
                strings.append(author_icon)
        # Embed Title
        if (title := embed_dict.get("title")):
            strings.append(title)
        # Embed URL
        if (url := embed_dict.get("url")):
            strings.append(url)
        # Embed Description
        if (description := embed_dict.get("description")):
            strings.append(description)
        # Embed Thumbnail
        if (thumbnail := embed_dict.get("thumbnail")):
            strings.append(thumbnail['url'])
        # Embed Fields
        if (fields := embed_dict.get("fields")):
            for field in fields:
                strings.extend([field['name'], field['value']])
        # Embed Image
        if (image := embed_dict.get("image")):
            strings.append(image['url'])
        # Embed Footer
        if (footer := embed_dict.get("footer")):
            strings.append(footer['text'])
            if (footer_url := footer.get("icon_url")):
                strings.append(footer_url)

        return "  ".join(strings)


def setup(bot):
    bot.add_cog(StalkingEvents(bot))
