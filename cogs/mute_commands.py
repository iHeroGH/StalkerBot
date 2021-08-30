from discord.ext import commands
import voxelbotutils as vbu

from datetime import datetime as dt, timedelta


class MuteCommands(vbu.Cog, name="Mute Commands"):

    def __init__(self, bot):
        self.bot = bot

    @vbu.command(aliases=['tm', 'mute'])
    async def tempmute(self, ctx, time:int, unit:str="m"):
        """Temporarily mutes the bot from sending a user DMs for a specificed amount of time"""
        unit = unit.lower()

        # Checks that units are valid
        valid_units = {
            "s": 1,
            "m": 60,
            "h": 60 * 60,
            "d": 60 * 60 * 24,
        }

        if unit not in valid_units.keys():
            return await ctx.send("You didn't provide a valid unit (s, m, h, d)")

        # Checks that time is above 0
        if time <= 0:
            return await ctx.send("The time value you provided is under 0 seconds")

        # Change all time into seconds
        seconded_time = valid_units[unit] * time

        # Add time
        future = dt.utcnow() + timedelta(seconds=seconded_time)

        # Add to database
        async with vbu.Database() as db:
            await db("INSERT INTO tempmute VALUES($1, $2) ON CONFLICT (userid) DO UPDATE SET time = $2;", ctx.author.id, future)

        await ctx.send(f"I won't send you messages for the next `{time}{unit}`")

    @vbu.command(aliases=['unm', "um"])
    async def unmute(self, ctx):
        """Unmutes StalkerBot from sending a user messages"""

        # Remove the user from the tempmute database
        async with vbu.Database() as db:
            await db("DELETE FROM tempmute WHERE userid=$1;", ctx.author.id)

        await ctx.send("Unmuted StalkerBot.")


def setup(bot):
    bot.add_cog(MuteCommands(bot))
