import sys
from importlib import metadata

import novus as n
from novus import types as t
from novus.ext import client

from .stalker_utils.misc_utils import split_action_rows
from .stalker_utils.stalker_cache_utils import count_keywords, count_stalkers


class MiscCommands(client.Plugin):

    INVITE_LINK = (
        r"https://discord.com/api/oauth2/authorize?" +
        r"client_id=723813550136754216&" +
        r"permissions=1024&scope=applications.commands+bot"
    )
    SUPPORT_SERVER = r"https://discord.gg/voxelfox"
    GIT_LINK = r"https://github.com/iHeroGH/StalkerBot"
    DONATION_LINK = r"https://upgrade.chat/208895639164026880/shop"
    VOTE_LINK = r"https://top.gg/bot/723813550136754216/vote"

    HELP_TEXT = (
        "StalkerBot is just a simple bot that sends you a DM every time a " +
        "keyword that you set is said in a channel you have access to!\n\n\n" +

        "Your **keywords** are *global*, but you can set " +
        "*server-specific* keywords aswell.\n\n" +

        "Finally, you can add **filters** for certain *users*, " +
        "*text phrases*, *channels*, and *servers*. These filters prevent " +
        "you from getting DMed about your keyword if it's said by a " +
        "specific user, in a specific text phrase, in a specific channel, " +
        "or in a specific server.\n\n\n" +

        "TL;DR: Get a DM every time your name is said! " +
        "- run {} to start."
    )
    EXAMPLE_IMAGE = (
        r"https://cdn.discordapp.com/attachments/649715200890765345/" +
        r"1204293095039041606/eQt84iC.png?ex=65d43458&is=65c1bf58&" +
        r"hm=aae500b5b8bb7cfe0adcd9b3da06e24081f43d6a5ddb458845dffd6c91b30d67&"
    )

    PRIVACY_POLICY = (
        "While the name of the bot may be slightly misleading, StalkerBot " +
        "is dedicated to keeping users' privacy safe:\n"

        "- StalkerBot never saves your messages outside of Discord.\n" +

        "- StalkerBot only sends messages to other users if a keyword is " +
        "said in those messages (or if the message is a reply).\n" +

        "- Users can opt-out of triggering others' keywords and receiving " +
        "messages for their own keywords\n\n"

        "To opt out, run the {} command\n" +
        "To opt back in, run the {} command\n" +
        "All users are opted in by default."
    )

    @client.command(name="invite")
    async def invite(self, ctx: t.CommandI) -> None:
        """Sends an invite link for the bot"""
        await ctx.send(self.INVITE_LINK)

    @client.command(name="info")
    async def info(self, ctx: t.CommandI) -> None:
        """Sends an informative message about the bot"""
        info_embed = n.Embed(title="StalkerBot Information")

        # Description and image
        info_embed.description = self.HELP_TEXT.format(
            self.bot.get_command("keyword add").mention  # type: ignore
        )
        info_embed.set_image(self.EXAMPLE_IMAGE)

        # Buttons
        buttons = [
            n.Button(
                label="Invite",
                custom_id="",
                style=n.ButtonStyle.URL,
                url=self.INVITE_LINK
            ),
            n.Button(
                label="Support Server",
                custom_id="",
                style=n.ButtonStyle.URL,
                url=self.SUPPORT_SERVER
            ),
            n.Button(
                label="Git",
                custom_id="",
                style=n.ButtonStyle.URL,
                url=self.GIT_LINK
            ),
            n.Button(
                label="Donate",
                custom_id="",
                style=n.ButtonStyle.URL,
                url=self.DONATION_LINK
            ),
            n.Button(
                label="Vote",
                custom_id="",
                style=n.ButtonStyle.URL,
                url=self.VOTE_LINK
            )
        ]

        await ctx.send(
            embeds=[info_embed], components=split_action_rows(buttons, 5)
        )

    @client.command(
        name="stats",
        guild_ids=[649715200890765342],  # 208895639164026880],
        default_member_permissions=n.Permissions(manage_guild=True)
    )
    async def stats(self, ctx: t.CommandI) -> None:
        """Sends some statistics about the bot"""
        stats_embed = n.Embed(title="StalkerBot Statistics")

        stats_embed.add_field(
            name="Creator",
            value="<@322542134546661388>\nhero.py\n322542134546661388",
            inline=False
        )

        novus_meta = metadata.metadata("novus")
        stats_embed.add_field(
            name="Library",
            value=(
                f"Python `{sys.version.split(' ', 1)[0]}`\n"
                f"[Novus]({novus_meta['Home-page']}) " +
                f"`{novus_meta['Version']}`\n"
            ),
            inline=False
        )

        stats_embed.add_field(
            name="Guild Count",
            value=str(len(self.bot.guilds))
        )
        stats_embed.add_field(
            name="User Count",
            value=str(count_stalkers())
        )
        stats_embed.add_field(
            name="Keyword Count",
            value=str(count_keywords())
        )

        await ctx.send(embeds=[stats_embed])

    @client.command(name="privacy")
    async def privacy(self, ctx: t.CommandI) -> None:
        """Sends the bot's privacy policy"""
        privacy_embed = n.Embed(title="StalkerBot Privacy Policy")

        privacy_embed.description = self.PRIVACY_POLICY.format(
            self.bot.get_command("opt out").mention,  # type: ignore
            self.bot.get_command("opt in").mention  # type: ignore
        )

        await ctx.send(embeds=[privacy_embed])
