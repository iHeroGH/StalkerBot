import novus as n
from novus import types as t
from novus.utils.times import utcnow as n_utcnow, format_timestamp
from novus.ext import client, database as db

from datetime import datetime as dt

from .stalker_utils.stalker_cache_utils import mute_modify_cache_db
from .stalker_utils.misc import get_datetime_until

class MuteCommands(client.Plugin):

    @client.command(
        name="mute",
        options = [
            n.ApplicationCommandOption(
                name="time",
                type=n.ApplicationOptionType.string,
                description="The amount of time to mute for ('number'(smhdy))"
            ),
        ]
    )
    async def mute(self, ctx: t.CommandI, time: str) -> None:
        """Mutes the bot for some time."""

        mute_until = get_datetime_until(time)

        async with db.Database.acquire() as conn:
            success = await mute_modify_cache_db(
                ctx.user.id, dt.utcnow() + mute_until, conn
            )

        if not success:
            return await ctx.send("Something went wrong trying to mute")

        await ctx.send(
            f"Muting until " +
            f"{format_timestamp(n_utcnow() + mute_until)}"
        )

    @client.command(name="unmute")
    async def unmute(self, ctx: t.CommandI) -> None:
        """Unmutes the bot if it was already muted."""

        async with db.Database.acquire() as conn:
            success = await mute_modify_cache_db(ctx.user.id, None, conn)

        if not success:
            return await ctx.send(
                "Something went wrong trying to unmute, " +
                "the bot may have already been unmuted."
            )

        await ctx.send("Successfuly unmuted!")

    @client.command(name="opt_out")
    async def opt_out(self, ctx: t.CommandI) -> None:
        """Opts-Out of the bot's features."""
        ...

    @client.command(name="opt_in")
    async def opt_in(self, ctx: t.CommandI) -> None:
        """Opts-In to the bot's features."""
        ...