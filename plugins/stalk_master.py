import logging
import re
from datetime import datetime

import novus as n
from novus.ext import client
from novus.ext import database as db

from .stalker_utils.stalker_cache_utils import (channel_modify_cache_db,
                                                get_all_stalkers, get_stalker)
from .stalker_utils.stalker_objects import (Filter, FilterEnum, Keyword,
                                            KeywordEnum, Stalker)

log = logging.getLogger("plugins.stalk_master")

"""
Filters
Message can be regular, embedded, or a reply
Event could be regular or an edit
"""


class StalkMaster(client.Plugin):

    @client.event.message
    async def on_message(self, message: n.Message):
        await self.stalk_message(message)

    @client.event.message_edit
    async def on_message_edit(self, before: n.Message, after: n.Message):
        await self.stalk_message(after, before)

    async def stalk_message(
                self,
                message: n.Message,
                before: n.Message | None = None
            ):
        """The main hub for incoming message events for keywords"""

        # Bot isn't ready
        if not self.bot.is_ready:
            log.info("Tried stalking before bot became ready.")
            return

        # Message is a DM
        if not message.guild:
            return

        # Something wrong with the edited message provided
        if before and before.id != message.id:
            before = None

        # StalkerBot is the author
        if self.bot.me and message.author.id == self.bot.me.id:
            return

        # Ensure the author isn't opted out
        if not message.author.bot:
            possible_opter = get_stalker(message.author.id)
            if possible_opter.opted_out:
                log.info(
                    f"Skipping {possible_opter.user_id} since they opted out."
                )
                return

        # React with the eyes emoji on special servers
        await self.stalk_reaction(message)

        # Maintain a dictionary of the message's embeds
        # to its scannable content
        decoded_embeds = {}
        for embed in message.embeds:
            decoded_embeds[embed] = self.decode_embed(embed)

        # Maintain a set of users who have already been sent a message
        already_sent: set[Stalker] = set()

        # Easy access to the guild and channel
        guild = self.bot.get_guild(message.guild.id)
        assert guild
        channel = self.bot.get_channel(message.channel.id, True)

        # Check the message's reply
        message_reply = message.referenced_message
        if message_reply:
            success = await self.acknowledge_reply(
                message=message,
                reply=message_reply,
                guild=guild,
                channel=channel,
                already_sent=already_sent,
                is_edit=before is not None
            )

            if success:
                await self.send_trigger(
                    stalker := get_stalker(message_reply.author.id),
                    message=message,
                    guild=guild,
                    before=before,
                    triggered_keyword="",
                    triggering_embeds=[],
                    is_reply=True
                )
                already_sent.add(stalker)

        all_stalkers = get_all_stalkers()
        for stalker in all_stalkers:

            if not self.is_triggerable_stalker(
                stalker,
                already_sent=already_sent,
                message=message,
                member=await self.get_stalker_member(stalker, guild),
                guild=guild,
                channel=channel,
                is_reply=False,
                is_edit=before is not None
            ):
                continue

            # TODO: If a webhook sent the message, the webhook author will
            # not be in the guild

            log.debug("Continuing with triggerable stalker")
            for keyword_set in stalker.keywords.values():
                for keyword in keyword_set:
                    stalker_can = self.is_triggerable_stalker(
                        stalker,
                        already_sent=already_sent
                    )

                    if not stalker_can:
                        break

                    embeds_are = self.get_triggering_embeds(
                        stalker,
                        keyword,
                        decoded_embeds=decoded_embeds,
                        guild=guild,
                        channel=channel
                    )
                    kw_is = self.is_triggering(
                        stalker,
                        keyword,
                        content=message.content,
                        guild=guild,
                        channel=channel
                    )

                    if kw_is or embeds_are:
                        await self.send_trigger(
                            stalker,
                            message=message,
                            guild=guild,
                            before=before,
                            triggered_keyword=keyword.keyword,
                            triggering_embeds=embeds_are,
                            is_reply=False
                        )
                        already_sent.add(stalker)

    async def send_trigger(
                self,
                stalker: Stalker,
                *,
                message: n.Message,
                guild: n.Guild,
                before: n.Message | None = None,
                triggered_keyword: str = "",
                triggering_embeds: list[n.Embed] = [],
                is_reply: bool = False
            ):
        """
        The main hub for triggered keywords to be sent out to their
        respective users
        """

        log.info(
            f"Attempting to send to {stalker.user_id} " +
            f"message {message.id} by {message.author.id} " +
            f"{'with an edit ' if before else ''}" +
            f"{f'for `{triggered_keyword}` ' if triggered_keyword else ''}" +
            f"{'with embeds ' if triggering_embeds else ''}" +
            f"{'as a reply ' if is_reply else ''}"
        )

        message_payload = {
            "content": "",
            "embeds": []
        }

        if stalker.settings.embed_message:
            message_payload['embeds'].append(self.create_sendable_embed(
                message=message,
                before=before,
                triggered_keyword=triggered_keyword,
                triggering_embeds=triggering_embeds,
                is_reply=is_reply
            ))
        else:
            message_payload['content'] = self.create_sendable_string(
                message=message,
                before=before,
                triggered_keyword=triggered_keyword,
                triggering_embeds=triggering_embeds,
                is_reply=is_reply
            )

        message_payload['embeds'] += triggering_embeds[:9]

        where_to: n.Channel | n.GuildMember | None
        if stalker.dm_channel:
            if isinstance(stalker.dm_channel, int):
                stalker.dm_channel = n.Channel.partial(
                    self.bot.state, stalker.dm_channel
                )
            where_to = stalker.dm_channel
        else:
            where_to = await self.get_stalker_member(stalker, guild)

        if not where_to:
            log.info(
                    f"A DM channel could not be created for {stalker.user_id}"
                )
            return

        try:
            await where_to.send(**message_payload)
            log.info(f"Sent message {message.id} to {stalker.user_id}!")
        except n.errors.Forbidden:
            log.info(
                f"Stalker {stalker.user_id} has probably blocked StalkerBot."
            )

    async def acknowledge_reply(
                self,
                *,
                message: n.Message,
                reply: n.Message,
                guild: n.Guild,
                channel: n.Channel,
                is_edit: bool = False,
                already_sent: set[Stalker] = set()
            ) -> bool:
        """Deal with a message that replies to another message"""

        log.debug(f"Analyzing reply {reply.id} for message {message.id}")

        stalker = get_stalker(reply.author.id)
        member = await self.get_stalker_member(stalker, guild)

        if not stalker.used_keywords:
            return False

        if not member:
            return False

        if not self.is_triggerable_stalker(
            stalker,
            message=message,
            guild=guild,
            channel=channel,
            member=member,
            already_sent=already_sent,
            is_reply=True,
            is_edit=is_edit
        ):
            return False

        return True

    async def get_stalker_member(
                self,
                stalker: Stalker,
                guild: n.Guild,
            ) -> n.GuildMember | None:
        """Retrieves a member object via the API"""
        try:
            member = (
                guild.get_member(stalker.user_id) or None
                # await guild.fetch_member(stalker.user_id)
            )
            assert member
            if not stalker.dm_channel:
                channel = await member.create_dm_channel()

                async with db.Database.acquire() as conn:
                    await channel_modify_cache_db(
                        channel, stalker.user_id, conn
                    )
        except Exception:  # Member probably does not exist
            # log.error(
            #     "Something went wrong retrieving a Stalker " +
            #     f"({stalker.user_id}) for guild {guild.id}"
            # )
            return None

        return member

    def is_triggerable_stalker(
                self,
                stalker: Stalker,
                *,
                already_sent: set[Stalker] = set(),
                message: n.Message | None = None,
                member: n.GuildMember | None = None,
                guild: n.Guild | None = None,
                channel: n.Channel | None = None,
                is_reply: bool = False,
                is_edit: bool = False,
            ) -> bool:
        """
        A master conditional of the cases in which a stalker may be DMed
        a message
        """

        if stalker.opted_out:
            log.debug(f"Skipping {stalker.user_id}: Opted out.")
            return False

        if already_sent and stalker in already_sent:
            log.debug(f"Skipping {stalker.user_id}: Already sent.")
            return False

        if stalker.mute_until and datetime.utcnow() <= stalker.mute_until:
            log.debug(f"Skipping {stalker.user_id}: Muted.")
            return False

        if not stalker.settings.reply_trigger and is_reply:
            log.debug(f"Skipping {stalker.user_id}: Uninterested in replies.")
            return False

        if not stalker.settings.edit_trigger and is_edit:
            log.debug(f"Skipping {stalker.user_id}: Uninterested in edits.")
            return False

        if not message:
            log.debug(f"Continuing with {stalker.user_id}")
            return True

        if not stalker.settings.bot_trigger and message.author.bot:
            log.debug(f"Skipping {stalker.user_id}: Uninterested in bots.")
            return False

        if not stalker.settings.bot_trigger and \
                message.author.discriminator == "0000":
            log.debug(f"Skipping {stalker.user_id}: Uninterested in webhooks.")
            return False

        if not stalker.settings.self_trigger and \
                message.author.id == stalker.user_id:
            log.debug(f"Skipping {stalker.user_id}: Uninterested in self.")
            return False

        fake_user_filter = Filter(message.author.id, FilterEnum.user_filter)
        if fake_user_filter in stalker.filters[FilterEnum.user_filter]:
            log.debug(
                f"Skipping {stalker.user_id}: " +
                f"Uninterested in author {message.author.id}."
            )
            return False

        # If both are not given, then it's okay. But if one is given, the other
        # must also be given
        if not guild and not channel:
            return True
        assert guild and channel

        # Member is likely not in this guild
        if not member:
            return False

        # TODO: Deal with if we actually wanna pass the full Guild object or
        # if BaseGuild (message.guild) is enough

        if not channel.permissions_for(member).view_channel:
            log.debug(
                f"Skipping {stalker.user_id}: No permissions for {channel.id}."
            )
            return False

        fake_guild_filter = Filter(guild.id, FilterEnum.server_filter)
        if fake_guild_filter in stalker.filters[FilterEnum.server_filter]:
            log.debug(
                f"Skipping {stalker.user_id}: " +
                f"Uninterested in guild {guild.id}."
            )
            return False

        fake_channel_filter = Filter(channel.id, FilterEnum.channel_filter)
        if fake_channel_filter in stalker.filters[FilterEnum.channel_filter]:
            log.debug(
                f"Skipping {stalker.user_id}: " +
                f"Uninterested in channel {channel.id}."
            )
            return False

        return True

    def get_triggering_embeds(
                self,
                stalker: Stalker,
                keyword: Keyword,
                *,
                decoded_embeds: dict[n.Embed, str],
                guild: n.Guild,
                channel: n.Channel
            ) -> list[n.Embed]:
        """
        Returns a list of embeds that successfully trigger keywords
        """

        triggering: list[n.Embed] = []
        for embed, embed_content in decoded_embeds.items():
            if self.is_triggering(
                stalker,
                keyword,
                content=embed_content,
                guild=guild,
                channel=channel
            ):
                triggering.append(embed)

        return triggering

    def is_triggering(
                self,
                stalker: Stalker,
                keyword: Keyword,
                *,
                content: str,
                guild: n.Guild,
                channel: n.Channel
            ) -> bool:
        """
        Checks if a string of content can be triggered without bypassing
        quotes or filters
        """
        if keyword.keyword_type == KeywordEnum.server_specific and \
                keyword.server_id != guild.id:
            log.debug(
                f"Skipping {stalker.user_id} for {keyword}: Server-Specific."
            )
            return False

        if keyword.keyword_type == KeywordEnum.channel_specific and \
                keyword.channel_id != channel.id:
            log.debug(
                f"Skipping {stalker.user_id} for {keyword}: Channel-Specific."
            )
            return False

        original_content = content

        if not stalker.settings.quote_trigger:
            non_quoted = [
                line
                for line in content.split("\n")
                if not line.startswith("> ")
            ]
            content = "\n".join(non_quoted)

        for text_filter in stalker.filters[FilterEnum.text_filter]:
            assert isinstance(text_filter.filter, str)

            content = re.sub(
                text_filter.filter.lower(), "", content.lower()
            )

        if keyword.keyword not in content.lower():
            if len(original_content) != len(content):
                log.debug(
                    f"Skipping {stalker.user_id} with keyword {keyword}: " +
                    "Text Filter/Quotes."
                )
            return False

        return True

    def create_sendable_embed(
                self,
                *,
                message: n.Message,
                before: n.Message | None = None,
                triggered_keyword: str = "",
                triggering_embeds: list[n.Embed] = [],
                is_reply: bool = False
            ) -> n.Embed:
        """Creates a nicely formatted embed to send to triggered Stalkers"""
        embed = n.Embed()
        embed.color = abs(hash(triggered_keyword)) & 0xffffff

        embed.set_author_from_user(message.author)

        if before:
            embed.add_field(
                name="Previous Content",
                value=before.content,
                inline=False
            )

        embed.add_field(
            name="Message Content",
            value=(
                message.content[:1900] if not triggering_embeds else
                "*Embeds attached*"
            ),
            inline=False
        )

        assert message.guild
        embed.add_field(
            name="Message Channel",
            value=(
                f"{message.channel.mention}\n" +
                f"({message.guild.name}: {message.channel.name})"
            ),
            inline=True
        )

        embed.add_field(
            name="Message Link",
            value=f"[Jump To Message]({message.jump_url})",
            inline=True
        )

        if message.attachments:
            embed.add_field(
                name="Attachment Links",
                value=self.extract_attachments(message),
                inline=False
            )

        if triggered_keyword:
            embed.set_footer(f"Keyword: {triggered_keyword}")

        if is_reply:
            embed.set_footer("Reply")

        embed.timestamp = message.timestamp

        return embed

    def create_sendable_string(
                self,
                *,
                message: n.Message,
                before: n.Message | None = None,
                triggered_keyword: str = "",
                triggering_embeds: list[n.Embed] = [],
                is_reply: bool = False
            ) -> str:
        """Creates an identifying string to send to triggered Stalkers"""

        author_identifier = (
            f"{message.author.mention} ({message.author.username})"
        )
        action_identifier = "typed"
        if before:
            action_identifier = "edited their message to include"
        if triggering_embeds:
            action_identifier = "sent an embedded message containing"
        if is_reply:
            action_identifier = "replied to your message"

        assert message.guild
        location_identifier = (
            f"the keyword `{triggered_keyword}` in " +
            f"{message.channel.mention} " +
            f"({message.guild.name}: {message.channel.name})"
        )

        full_message_identifier = (
            f"They typed `{message.content[:1900]}` " +
            f"<{message.jump_url}>"
        )
        if triggering_embeds:
            full_message_identifier = "Embeds Attached"

        sendable_message = (
            f"{author_identifier} {action_identifier} " +
            f"{location_identifier}. {full_message_identifier}."
        )

        if message.attachments:
            sendable_message += "\n" + self.extract_attachments(message)

        return sendable_message

    def extract_attachments(self, message: n.Message) -> str:
        attachment_links = [
                attachment.url for attachment in message.attachments
            ]
        attachment_text = ""
        for ind, link in enumerate(attachment_links):
            attachment_text += f"[Attachment {ind + 1}]({link})\n"

        return attachment_text

    def decode_embed(self, embed: n.Embed) -> str:
        """
        Given an embed, return a string of all its parts with a blacklisted
        character as a delimiter
        """
        decoded = ""
        for part in embed._to_data().values():
            if isinstance(part, list):
                for subpart in part:
                    if isinstance(subpart, dict):
                        decoded += self.decode_dict_part(subpart)

            elif isinstance(part, dict):
                decoded += self.decode_dict_part(part)

            else:
                decoded += str(part) + "`"

        return decoded

    def decode_dict_part(self, dict_part: dict) -> str:
        """
        Given a dictionary denoting an embed's parts, return a flattened,
        delimited string
        """
        decoded = ""
        for key in ["name", "value", "url", "icon_url"]:
            if key in dict_part:
                decoded += dict_part[key] + "`"

        return decoded

    async def stalk_reaction(self, message: n.Message):
        """Adds an eye emoji reaction to special servers"""
        targets = [649715200890765342, 208895639164026880]

        if message.guild and message.guild.id in targets:
            if "stalker" in message.content.replace(" ", "").lower():
                await message.add_reaction("👀")
                log.info("Stalker reaction added")
