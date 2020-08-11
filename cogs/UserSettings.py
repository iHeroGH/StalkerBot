import discord
from discord.ext import commands
import asyncpg
import asyncio
import aiohttp
import json


class UserSettings(commands.Cog, name = "User Setting Commands"):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def settings(self, ctx):
        """Allows users to change settings (such as OwnTrigger and QuoteTrigger"""


        connection = await asyncpg.connect(**self.bot.database_auth)
        existingSettings = await connection.fetch("select * from usersettings where userid = $1;", ctx.author.id)
        await connection.close()

        owntrigger = existingSettings['owntrigger']
        quotetrigger = existingSettings['quotetrigger']

        options = [
            f"1\N{COMBINING ENCLOSING KEYCAP}. Would you like to trigger your own keywords? (currently {owntrigger})",
            f"2\N{COMBINING ENCLOSING KEYCAP}. Would you like to be DMed if your keyword is said in a quote (> Message)? (currently {quotetrigger})"
        ]

        message = await ctx.send("\n".join(options))
        await message.add_reaction("1\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("2\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

        validEmoji = [
            "1\N{COMBINING ENCLOSING KEYCAP}",
            "2\N{COMBINING ENCLOSING KEYCAP}",
            "\N{WHITE HEAVY CHECK MARK}"
        ]

        x = True
        while x:
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in validEmoji

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Timed out!")
                return
            
            if reaction.emoji == validEmoji[0]:
                connection = await asyncpg.connect(**self.bot.database_auth)
                await connection.fetch("INSERT into usersettings (userid, owntrigger) VALUES ($1, $2) on conflict (userid) do update set owntrigger = $2", ctx.author.id, not owntrigger)
                await connection.close()
                await ctx.send(f"Can trigger own keywords? {not owntrigger}")
            elif reaction.emoji == validEmoji[1]:
                connection = await asyncpg.connect(**self.bot.database_auth)
                await connection.fetch("INSERT into usersettings (userid, quotetrigger) VALUES ($1, $2) on conflict (userid) do update set quotetrigger = $2", ctx.author.id, not quotetrigger)
                await connection.close()
                await ctx.send(f"Gets DMed from quotes? {not quotetrigger}")
            elif reaction.emoji == validEmoji[2]:
                x = False
                await ctx.send("Done!")
        

        

def setup(bot):
    bot.add_cog(UserSettings(bot))
