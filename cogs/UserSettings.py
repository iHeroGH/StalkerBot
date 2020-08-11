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

        # Get the current settings for a user
        connection = await asyncpg.connect(**self.bot.database_auth)
        existingSettings = await connection.fetch("select * from usersettings where userid = $1;", ctx.author.id)
        await connection.close()

        # Checks to see if existing settings for the user actually exist. If not, defaults to True
        if existingSettings:
            owntrigger = existingSettings[0]['owntrigger']
            quotetrigger = existingSettings[0]['quotetrigger']
        else:
            owntrigger = True
            quotetrigger = True

        # Options list so it looks good in the message
        options = [
            f"1\N{COMBINING ENCLOSING KEYCAP}. Would you like to trigger your own keywords? (currently {owntrigger})",
            f"2\N{COMBINING ENCLOSING KEYCAP}. Would you like to be DMed if your keyword is said in a quote (> Message)? (currently {quotetrigger})"
        ]

        # Sends the initial message
        message = await ctx.send("\n".join(options))
        # Reacts to the initial message with 1, 2, and check mark
        await message.add_reaction("1\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("2\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

        # List of valid emojis the user can react with 
        validEmoji = [
            "1\N{COMBINING ENCLOSING KEYCAP}",
            "2\N{COMBINING ENCLOSING KEYCAP}",
            "\N{WHITE HEAVY CHECK MARK}"
        ]

        # Loops until checkmark reaction is reacted to
        while True:

            # Checks that author is who typed the command and that the emoji reacted by the user is in validEmoji
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in validEmoji

            # Waits for the reaction from the user
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Timed out!")
                return
            
            # Checks which emoji was reacted and does the stuff
            if reaction.emoji == validEmoji[0]:
                connection = await asyncpg.connect(**self.bot.database_auth)
                await connection.fetch("INSERT into usersettings (userid, owntrigger) VALUES ($1, $2) on conflict (userid) do update set owntrigger = $2", ctx.author.id, not owntrigger)
                await connection.close()
                owntrigger = not owntrigger
            elif reaction.emoji == validEmoji[1]:
                connection = await asyncpg.connect(**self.bot.database_auth)
                await connection.fetch("INSERT into usersettings (userid, quotetrigger) VALUES ($1, $2) on conflict (userid) do update set quotetrigger = $2", ctx.author.id, not quotetrigger)
                await connection.close()
                quotetrigger = not quotetrigger
            #Ends the loop
            elif reaction.emoji == validEmoji[2]:
                await ctx.send("Done!")
                break
            newOptions = [
                f"1\N{COMBINING ENCLOSING KEYCAP}. Would you like to trigger your own keywords? (currently {owntrigger})",
                f"2\N{COMBINING ENCLOSING KEYCAP}. Would you like to be DMed if your keyword is said in a quote (> Message)? (currently {quotetrigger})"
            ]
            await message.edit(content=("\n".join(newOptions)), delete_after=3.0)
        

        

def setup(bot):
    bot.add_cog(UserSettings(bot))
