import logging
import re

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client

from.stalker_utils.stalker_cache_utils import get_all_stalkers, get_stalker
from .stalker_utils.stalker_objects import Stalker
from .stalker_utils.input_sanitizer import BLACKLISTED_CHARACTERS

log = logging.getLogger("plugins.stalk_master")

"""
Filters
Message can be regular, embedded, or a reply
Event could be regular or an edit
"""
class StalkMaster(client.Plugin):

    @client.event.message
    async def on_message(self, message: n.Message):
        print("Message Found!")
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

        # Maintain a dictionary of the message's embeds to its scannable content
        decoded_embeds = {}
        for embed in message.embeds:
            decoded_embeds[embed] = self.decode_embed(embed)

        # Maintain a set of users who have already been sent a message
        already_sent: set[Stalker] = set()
        all_stalkers = get_all_stalkers()

        # Easy access to the guild and channel
        guild = self.bot.get_guild(message.guild.id)
        assert guild
        channel = self.bot.get_channel(message.channel.id, True)

        # Check the message's reply
        message_reply = message.referenced_message
        if message_reply:
            success = await self.acknowledge_reply(
                message, message_reply, guild
            )

            if success:
                await self.send_trigger(
                    stalker:=get_stalker(message_reply.author.id),
                    message=message,
                    before=before,
                    triggered_keyword="",
                    triggering_embeds=list(decoded_embeds.keys()),
                    is_reply=True
                )
                already_sent.add(stalker)

    async def send_trigger(
                self,
                stalker: Stalker,
                *,
                message: n.Message,
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
            f"Sending {stalker.user_id} " +
            f"message {message.id} by {message.author.id} " +
            f"{'with an edit ' if before else ''}" +
            f"{f'for keyword {triggered_keyword} ' if triggered_keyword else ''}" +
            f"{'with embeds ' if triggering_embeds else ''}" +
            f"{'as a reply ' if is_reply else ''}"
        )
        return

    async def acknowledge_reply(
                self,
                message: n.Message,
                reply: n.Message,
                guild: n.Guild
            ) -> bool:
        """Deal with a message that replies to another message"""

        log.info(f"Analyzing reply {reply.id} for message {message.id}")
        # If this fails, OP is no longer a member of the guild
        try:
            author_member = await guild.fetch_member(reply.author.id)
            stalker = get_stalker(author_member.id)

            if stalker.opted_out or not stalker.settings.reply_trigger:
                return False

            if message.author.id == reply.author.id and not stalker.settings.self_trigger:
                return False

            if message.author.bot and not stalker.settings.bot_trigger:
                return False

        except:
            return False

        return True

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
                decoded += str(part) + BLACKLISTED_CHARACTERS[0]

        return decoded

    def decode_dict_part(self, dict_part: dict) -> str:
        """
        Given a dictionary denoting an embed's parts, return a flattened,
        delimited string
        """
        decoded = ""
        for key in ["name", "value", "url", "icon_url"]:
            if key in dict_part:
                decoded += dict_part[key] + BLACKLISTED_CHARACTERS[0]

        return decoded

    async def stalk_reaction(self, message: n.Message):
        """Adds an eye emoji reaction to special servers"""
        targets = [649715200890765342, 208895639164026880]

        if message.guild and message.guild.id in targets:
            if "stalker" in message.content.replace(" ", "").lower():
                await message.add_reaction("👀")
                log.info("Stalker reaction added")