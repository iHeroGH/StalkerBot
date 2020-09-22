import asyncio

from discord.ext import commands
import asyncpg


class UserSettings(commands.Cog, name="User Setting Commands"):

    def __init__(self, bot):
        self.bot = bot



    @commands.command(aliases=['qs', 'quicksettings', 'quicksetup'])
    async def quickswitch(self, ctx, setting=None):
        """Allows users to change individual settings quickly"""

        # Checks if the setting provided is an existing setting
        if setting == None:
            return await ctx.send("You didn't select a valid setting to switch. The available settings are `owntrigger`, `quotetrigger`, and `embedmessage`.")
        if setting.lower() != "owntrigger" and setting.lower() != "quotetrigger" and setting.lower() != "embedmessage":
            return await ctx.send("You didn't select a valid setting to switch. The available settings are `owntrigger`, `quotetrigger`, and `embedmessage`.")

        # Get the current settings for a user
        async with self.bot.database() as db:
            existingSettings = await db("select * from usersettings where userid = $1;", ctx.author.id)

        # Checks to see if existing settings for the user actually exist. If not, defaults to True
        if existingSettings:
            owntrigger = existingSettings[0]['owntrigger']
            quotetrigger = existingSettings[0]['quotetrigger']
            embedmessage = existingSettings[0]['embedmessage']
        else:
            owntrigger = True
            quotetrigger = True
            embedmessage = False

        # Updates the selected setting (switches it from whatever it is now to the opposite)
        if setting.lower() == "owntrigger":
            async with self.bot.database() as db:
                await db("INSERT into usersettings (userid, owntrigger) VALUES ($1, $2) on conflict (userid) do update set owntrigger = $2", ctx.author.id, not owntrigger)
            await ctx.send(f"Updated `owntrigger` from `{owntrigger}` to `{not owntrigger}`")
        elif setting.lower() == "quotetrigger":
            async with self.bot.database() as db:
                await db("INSERT into usersettings (userid, quotetrigger) VALUES ($1, $2) on conflict (userid) do update set quotetrigger = $2", ctx.author.id, not quotetrigger)  
            await ctx.send(f"Updated `quotetrigger` from `{quotetrigger}` to `{not quotetrigger}`")
        elif setting.lower() == "embedmessage":
            async with self.bot.database() as db:
                await db("INSERT into usersettings (userid, embedmessage) VALUES ($1, $2) on conflict (userid) do update set embedmessage = $2", ctx.author.id, not embedmessage)
            await ctx.send(f"Updated `embedmessage` from `{embedmessage}` to `{not embedmessage}`")



    @commands.command(aliases=['setup'])
    async def settings(self, ctx):
        """Allows users to change settings (such as OwnTrigger, QuoteTrigger, and EmbedMessage)"""

        # Get the current settings for a user
        async with self.bot.database() as db:
            existingSettings = await db("select * from usersettings where userid = $1;", ctx.author.id)

        # Checks to see if existing settings for the user actually exist. If not, defaults to True
        if existingSettings:
            owntrigger = existingSettings[0]['owntrigger']
            quotetrigger = existingSettings[0]['quotetrigger']
            embedmessage = existingSettings[0]['embedmessage']
        else:
            owntrigger = True
            quotetrigger = True
            embedmessage = False

        # Options list so it looks good in the message
        options = [
            f"1\N{COMBINING ENCLOSING KEYCAP} Would you like to trigger your own keywords? (currently {owntrigger})",
            f"2\N{COMBINING ENCLOSING KEYCAP} Would you like to be DMed if your keyword is said in a quote? (currently {quotetrigger})",
            f"3\N{COMBINING ENCLOSING KEYCAP} Would you like the DMs to be embedded? (currently {embedmessage})"
        ]

        # Sends the initial message
        message = await ctx.send("\n".join(options))
        # Reacts to the initial message with 1, 2, and check mark
        await message.add_reaction("1\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("2\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("3\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

        # List of valid emojis the user can react with
        validEmoji = [
            "1\N{COMBINING ENCLOSING KEYCAP}",
            "2\N{COMBINING ENCLOSING KEYCAP}",
            "3\N{COMBINING ENCLOSING KEYCAP}",
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
                async with self.bot.database() as db:
                    await db("INSERT into usersettings (userid, owntrigger) VALUES ($1, $2) on conflict (userid) do update set owntrigger = $2", ctx.author.id, not owntrigger)
                owntrigger = not owntrigger
            elif reaction.emoji == validEmoji[1]:
                async with self.bot.database() as db:
                    await db("INSERT into usersettings (userid, quotetrigger) VALUES ($1, $2) on conflict (userid) do update set quotetrigger = $2", ctx.author.id, not quotetrigger)  
                quotetrigger = not quotetrigger
            elif reaction.emoji == validEmoji[2]:
                async with self.bot.database() as db:
                    await db("INSERT into usersettings (userid, embedmessage) VALUES ($1, $2) on conflict (userid) do update set embedmessage = $2", ctx.author.id, not embedmessage)
                embedmessage = not embedmessage
            elif reaction.emoji == validEmoji[3]:
                break

            newOptions = [
                f"1\N{COMBINING ENCLOSING KEYCAP} Would you like to trigger your own keywords? (currently {owntrigger})",
                f"2\N{COMBINING ENCLOSING KEYCAP} Would you like to be DMed if your keyword is said in a quote? (currently {quotetrigger})",
                f"3\N{COMBINING ENCLOSING KEYCAP} Would you like the DMs to be embedded? (currently {embedmessage})"
            ]
            await message.edit(content=("\n".join(newOptions)))

        await ctx.send("Done!")
        await message.delete(delay=1.0)


def setup(bot):
    bot.add_cog(UserSettings(bot))
