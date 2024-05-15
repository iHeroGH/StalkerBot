from datetime import datetime as dt

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db
from novus.utils.times import format_timestamp
from novus.utils.times import utcnow as n_utcnow

from .stalker_utils.misc_utils import get_datetime_until
from .stalker_utils.stalker_cache_utils import (mute_modify_cache_db,
                                                opt_modify_cache_db)


class MuteCommands(client.Plugin):

    @client.command(
        name="mute",
        options=[
            n.ApplicationCommandOption(
                name="time",
                type=n.ApplicationOptionType.STRING,
                description="The amount of time to mute for ('number'(smhdy))"
            ),
        ]
    )
    async def mute(self, ctx: t.CommandI, time: str) -> None:
        """Mutes the bot for some time."""

        mute_until = get_datetime_until(time)

        async with db.Database.acquire() as conn:
            success = await mute_modify_cache_db(
                dt.utcnow() + mute_until, ctx.user.id, conn
            )

        if not success:
            return await ctx.send(
                "Something went wrong trying to mute.", ephemeral=True
            )

        await ctx.send(
            "Muting until " +
            f"{format_timestamp(n_utcnow() + mute_until)}",
            ephemeral=True
        )

    @client.command(name="unmute")
    async def unmute(self, ctx: t.CommandI) -> None:
        """Unmutes the bot if it was already muted."""

        async with db.Database.acquire() as conn:
            success = await mute_modify_cache_db(None, ctx.user.id, conn)

        if not success:
            return await ctx.send(
                "Something went wrong trying to unmute, " +
                "the bot may have already been unmuted.", ephemeral=True
            )

        await ctx.send("Successfully unmuted!", ephemeral=True)

    @client.command(name="opt out")
    async def opt_out(self, ctx: t.CommandI) -> None:
        """Opts-Out of the bot's features."""

        async with db.Database.acquire() as conn:
            success = await opt_modify_cache_db(True, ctx.user.id, conn)

        if not success:
            return await ctx.send(
                "Something went wrong trying to opt-out, " +
                "you may already be opted-out of the bot's features.",
                ephemeral=True
            )

        await ctx.send("Successfully opted-out!", ephemeral=True)

    @client.command(name="opt in")
    async def opt_in(self, ctx: t.CommandI) -> None:
        """Opts-In to the bot's features."""

        async with db.Database.acquire() as conn:
            success = await opt_modify_cache_db(False, ctx.user.id, conn)

        if not success:
            return await ctx.send(
                "Something went wrong trying to opt-in, " +
                "you may already be opted-in to the bot's features.",
                ephemeral=True
            )

        await ctx.send("Successfully opted-in!", ephemeral=True)
