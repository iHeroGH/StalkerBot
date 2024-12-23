import logging

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db

from .stalker_utils.autocomplete import SETTING_OPTIONS
from .stalker_utils.misc_utils import split_action_rows
from .stalker_utils.stalker_cache_utils import (get_stalker,
                                                settings_modify_cache_db)

log = logging.getLogger("plugins.user_settings")


class UserSettings(client.Plugin):

    # A map of the setting abbreviation to a description
    SETTING_DESCRIPTORS = {
        "self_trigger": (
            "Should you trigger your own keywords?"
        ),
        "quote_trigger": (
            "Should you get a DM if your keyword is said in a `>` quote?"
        ),
        "reply_trigger": (
            "Should you get a DM if a user replies to your message?"
        ),
        "bot_trigger": (
            "Should bots trigger your keywords?"
        ),
        "edit_trigger": (
            "Should you get a DM if a user edits a message with a keyword?"
        ),
        "embed_message": (
            "Should your DMs be embedded?"
        )
    }

    @client.event.filtered_component(r"SETTINGS \d+ .+")
    async def setting_pressed_event(self, ctx: t.ComponentI) -> None:
        log.info(f"Settings button pressed: {ctx.data.custom_id}")

        _, required_id, setting = ctx.data.custom_id.split(" ")

        if int(required_id) != ctx.user.id:
            return await ctx.send(
                "You can't interact with this button, run " +
                f"{self.settings.mention} to get buttons you can press",
                ephemeral=True
            )

        stalker = get_stalker(ctx.user.id)
        async with db.Database.acquire() as conn:
            await settings_modify_cache_db(
                ctx.user.id,
                setting,
                not stalker.settings.__getattribute__(setting),
                conn
            )

        embed, buttons = self.create_settings_menu(ctx.user.id)
        await ctx.update(
            embeds=[embed], components=split_action_rows(buttons, 5)
        )

    @client.event.filtered_component(r"SETTINGS_CANCEL \d+")
    async def setting_cancelled_event(self, ctx: t.ComponentI) -> None:
        log.info(f"Settings button pressed: {ctx.data.custom_id}")

        _, required_id = ctx.data.custom_id.split(" ")

        if int(required_id) != ctx.user.id:
            return await ctx.send(
                "You can't interact with this button, run " +
                f"{self.settings.mention} to get buttons you can press",
                ephemeral=True
            )

        await ctx.update(components=[])

    @client.command(name="settings")
    async def settings(self, ctx: t.CommandI) -> None:
        """Lets you see and modify your settings"""
        embed, buttons = self.create_settings_menu(ctx.user.id)
        await ctx.send(
            embeds=[embed], components=split_action_rows(buttons, 5),
            ephemeral=True
        )

    @client.command(
        name="quickswitch",
        options=[
            n.ApplicationCommandOption(
                name="setting",
                type=n.ApplicationOptionType.STRING,
                description="The setting you want to flip",
                choices=SETTING_OPTIONS
            ),
        ]
    )
    async def quick_switch(self, ctx: t.CommandI, setting: str) -> None:
        """Lets you quickly change one of your settings"""
        stalker = get_stalker(ctx.user.id)

        async with db.Database.acquire() as conn:
            success = await settings_modify_cache_db(
                ctx.user.id,
                setting,
                not stalker.settings.__getattribute__(setting),
                conn
            )

        if not success:
            return await ctx.send(
                "Ran into some trouble changing that setting, " +
                "it may not be an available setting.", ephemeral=True
            )

        # Send a confirmation message
        await ctx.send(
            f"Updated the `{setting}` setting to " +
            f"`{stalker.settings.__getattribute__(setting)}`",
            ephemeral=True
        )

    def create_settings_menu(
                self,
                user_id: int
            ) -> tuple[n.Embed, list[n.Button]]:
        """Returns the menu and buttons for the user settings"""

        # Get the stalker and their current settings
        stalker = get_stalker(user_id)
        current_settings = stalker.settings

        settings_menu = n.Embed(
            title="Settings"
        )
        settings_menu.description = ""
        settings_buttons = []
        for setting, description in self.SETTING_DESCRIPTORS.items():
            current_value = current_settings.__getattribute__(setting)

            settings_menu.description += "- " + description
            settings_menu.description += f" (currently **{current_value}**)\n"

            button_style = (
                n.ButtonStyle.DANGER if not current_value else
                n.ButtonStyle.GREEN
            )

            settings_buttons.append(n.Button(
                label=setting.replace("_", " ").title(),
                custom_id=f"SETTINGS {user_id} {setting}",
                style=button_style
            ))

        settings_buttons.append(n.Button(
                label="Done",
                custom_id=f"SETTINGS_CANCEL {user_id}",
                style=n.ButtonStyle.BLURPLE
            )
        )

        return settings_menu, settings_buttons
