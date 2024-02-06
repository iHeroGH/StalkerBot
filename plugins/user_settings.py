import logging
import typing

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client, database as db

from .stalker_utils.stalker_cache_utils import settings_modify_cache_db, \
                                                get_stalker

log = logging.getLogger("plugins.user_settings")

class UserSettings(client.Plugin):

    # A map of the setting abbreviation to a
    # (full description, whether or not it needs a menu)
    SETTING_DESCRIPTORS = {
        "self_trigger": (
            "Should you trigger your own keywords?",
            False
        ),
        "quote_trigger": (
            "Should you get a DM if your keyword is said in a `>` quote?",
            False
        ),
        "reply_trigger": (
            "Should you get a DM if a user replies to your message?",
            False
        ),
        "bot_trigger": (
            "Should bots trigger your keywords?",
            False
        ),
        "edit_trigger": (
            "Should you get a DM if a user edits a message with a keyword?",
            False
        ),
        "embed_message": (
            "Should your DMs be embedded?",
            False
        ),
    }

    @client.event.filtered_component(r"SETTINGS \d+ .+ \d")
    async def setting_pressed_event(self, ctx: t.ComponentI) -> None:
        log.info(f"Settings button pressed: {ctx.data.custom_id}")

        _, required_id, setting, is_menu = ctx.data.custom_id.split(" ")
        is_menu = int(is_menu)

        if int(required_id) != ctx.user.id:
            return await ctx.send(
                "You can't interact with this button, run " +
                f"{self.settings.mention} to get buttons you can press",
                ephemeral=True
            )

        stalker = get_stalker(ctx.user.id)
        if not is_menu:
            async with db.Database.acquire() as conn:
                await settings_modify_cache_db(
                    ctx.user.id,
                    setting,
                    not stalker.settings.__getattribute__(setting),
                    conn
                )

        embed, buttons = self.create_settings_menu(ctx.user.id)
        await ctx.update(
            embeds=[embed], components=self.split_action_rows(buttons, 5)
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
            embeds=[embed], components=self.split_action_rows(buttons, 5),
            ephemeral=True
        )

    @client.command(name="quick_switch")
    async def quick_switch(self, ctx: t.CommandI) -> None:
        """Lets you quickly change one of your settings"""
        return

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
        for setting, (description, is_menu) in self.SETTING_DESCRIPTORS.items():
            current_value = current_settings.__getattribute__(setting)

            settings_menu.description += "- " + description
            settings_menu.description += f" (currently **{current_value}**)\n"

            button_style = n.ButtonStyle.gray
            if not is_menu:
                button_style = n.ButtonStyle.danger if not current_value \
                                else n.ButtonStyle.green

            settings_buttons.append(n.Button(
                label=setting.replace("_", " ").title(),
                custom_id=f"SETTINGS {user_id} {setting} {int(is_menu)}",
                style=button_style
            ))

        settings_buttons.append(n.Button(
                label="Done",
                custom_id=f"SETTINGS_CANCEL {user_id}",
                style=n.ButtonStyle.blurple
            )
        )

        return settings_menu, settings_buttons

    def split_action_rows(
                self,
                buttons: list[n.Button],
                n_in_row: int
            ) -> list[n.ActionRow]:
        """Splits a given list of buttons into rows"""
        action_rows: list[n.ActionRow] = []
        current_row = n.ActionRow()
        for button in buttons:
            if len(current_row.components) < n_in_row:
                current_row.components.append(button)
            else:
                action_rows.append(current_row)
                current_row = n.ActionRow([button])

        if current_row.components:
            action_rows.append(current_row)

        return action_rows