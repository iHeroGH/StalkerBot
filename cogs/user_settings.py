import asyncio

from discord.ext import commands, vbu


class UserSettings(vbu.Cog, name="User Setting Commands"):

    @commands.command(aliases=['qs', 'quicksettings', 'quicksetup'])
    async def quickswitch(self, ctx, setting:str|None=None):
        """Allows users to change individual settings quickly"""

        # See if they provided a valid setting
        valid_settings = ("owntrigger", "quotetrigger", "embedmessage", "editmessage","bottrigger","replymessage",)
        if setting is None or setting.lower() not in valid_settings:
            return await ctx.send("You didn't select a valid setting to switch. The available settings are `owntrigger`, `quotetrigger`, `embedmessage`, `editmessage`, `bottrigger`, and `replymessage`.")
        setting = setting.lower()

        # Get the current settings for a user
        db = await self.bot.database.get_connection()
        current_settings_rows = await db("SELECT * from user_settings WHERE user_id=$1;", ctx.author.id)

        # See what their current settings are
        if current_settings_rows:
            current_settings = dict(current_settings_rows[0])
        else:
            current_settings = {
                'owntrigger': True,
                'quotetrigger': True,
                'embedmessage': False,
                'editmessage': True,
                'bottrigger': True,
                'replymessage': False
            }

        # Update settings
        updated_settings = current_settings.copy()
        updated_settings[setting] = not current_settings[setting]

        # Run database query
        await db(
            """INSERT INTO user_settings (user_id, owntrigger, quotetrigger, embedmessage, bottrigger, replymessage) VALUES
            ($1, $2, $3, $4, $5, $6) ON conflict (user_id) DO UPDATE SET owntrigger=$2, quotetrigger=$3, embedmessage=$4, editmessage=$5, bottrigger=$6, replymessage=$7""",
            ctx.author.id, updated_settings['owntrigger'], updated_settings['quotetrigger'], updated_settings['embedmessage'], updated_settings['editmessage'], updated_settings['bottrigger'], updated_settings['replymessage'],
        )
        await db.disconnect()

        # Tell the user it's done :D
        await ctx.send(f"Updated `{setting}` - now {'enabled' if updated_settings[setting] else 'disabled'}.")

    @commands.command(aliases=['setup', 'usersettings'])
    async def settings(self, ctx):
        """Allows users to change their settings"""

        # Get the current settings for a user
        async with vbu.Database() as db:
            existing_settings = await db("SELECT * FROM user_settings WHERE user_id = $1;", ctx.author.id)

        # Checks to see if existing settings for the user actually exist. If not, defaults to True
        if existing_settings:
            owntrigger = existing_settings[0]['owntrigger']
            quotetrigger = existing_settings[0]['quotetrigger']
            embedmessage = existing_settings[0]['embedmessage']
            editmessage = existing_settings[0]['editmessage']
            bottrigger = existing_settings[0]['bottrigger']
            replymessage = existing_settings[0]['replymessage']
        else:
            owntrigger = True
            quotetrigger = True
            embedmessage = False
            editmessage = True
            bottrigger = True
            replymessage = False

        # Options list so it looks good in the message
        options = [
            f"1\N{COMBINING ENCLOSING KEYCAP} Would you like to trigger your own keywords? (currently {owntrigger})",
            f"2\N{COMBINING ENCLOSING KEYCAP} Would you like to be DMed if your keyword is said in a quote? (currently {quotetrigger})",
            f"3\N{COMBINING ENCLOSING KEYCAP} Would you like the DMs to be embedded? (currently {embedmessage})",
            f"4\N{COMBINING ENCLOSING KEYCAP} Would you like to be DMed on message edits? (currently {editmessage})",
            f"5\N{COMBINING ENCLOSING KEYCAP} Would you like your keywords to get triggered by bots? (currently {bottrigger})",
            f"6\N{COMBINING ENCLOSING KEYCAP} Would you like to be DMed when a message you sent is replied to? (currently {replymessage})"
        ]

        # Sends the initial message
        message = await ctx.send("\n".join(options))
        # Reacts to the initial message with 1, 2, and check mark
        await message.add_reaction("1\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("2\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("3\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("4\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("5\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("6\N{COMBINING ENCLOSING KEYCAP}")
        await message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

        # List of valid emojis the user can react with
        valid_emoji = [
            "1\N{COMBINING ENCLOSING KEYCAP}",
            "2\N{COMBINING ENCLOSING KEYCAP}",
            "3\N{COMBINING ENCLOSING KEYCAP}",
            "4\N{COMBINING ENCLOSING KEYCAP}",
            "5\N{COMBINING ENCLOSING KEYCAP}",
            "6\N{COMBINING ENCLOSING KEYCAP}",
            "\N{WHITE HEAVY CHECK MARK}"
        ]

        # Loops until checkmark reaction is reacted to
        while True:

            # Checks that author is who typed the command and that the emoji reacted by the user is in valid_emoji
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in valid_emoji

            # Waits for the reaction from the user
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("Timed out!")
                return

            # Checks which emoji was reacted and does the stuff
            if reaction.emoji == valid_emoji[0]:
                async with vbu.Database() as db:
                    await db("INSERT INTO user_settings (user_id, owntrigger) VALUES ($1, $2) on conflict (user_id) do update set owntrigger = $2", ctx.author.id, not owntrigger)
                owntrigger = not owntrigger
            elif reaction.emoji == valid_emoji[1]:
                async with vbu.Database() as db:
                    await db("INSERT INTO user_settings (user_id, quotetrigger) VALUES ($1, $2) on conflict (user_id) do update set quotetrigger = $2", ctx.author.id, not quotetrigger)
                quotetrigger = not quotetrigger
            elif reaction.emoji == valid_emoji[2]:
                async with vbu.Database() as db:
                    await db("INSERT INTO user_settings (user_id, embedmessage) VALUES ($1, $2) on conflict (user_id) do update set embedmessage = $2", ctx.author.id, not embedmessage)
                embedmessage = not embedmessage
            elif reaction.emoji == valid_emoji[3]:
                async with vbu.Database() as db:
                    await db("INSERT INTO user_settings (user_id, editmessage) VALUES ($1, $2) on conflict (user_id) do update set editmessage = $2", ctx.author.id, not editmessage)
                editmessage = not editmessage
            elif reaction.emoji == valid_emoji[4]:
                async with vbu.Database() as db:
                    await db("INSERT INTO user_settings (user_id, bottrigger) VALUES ($1, $2) on conflict (user_id) do update set bottrigger = $2", ctx.author.id, not bottrigger)
                bottrigger = not bottrigger
            elif reaction.emoji == valid_emoji[5]:
                async with vbu.Database() as db:
                    await db("INSERT INTO user_settings (user_id, replymessage) VALUES ($1, $2) on conflict (user_id) do update set replymessage = $2", ctx.author.id, not replymessage)
                replymessage = not replymessage
            elif reaction.emoji == valid_emoji[6]:
                break

            new_options = [
                f"1\N{COMBINING ENCLOSING KEYCAP} Would you like to trigger your own keywords? (currently {owntrigger})",
                f"2\N{COMBINING ENCLOSING KEYCAP} Would you like to be DMed if your keyword is said in a quote? (currently {quotetrigger})",
                f"3\N{COMBINING ENCLOSING KEYCAP} Would you like the DMs to be embedded? (currently {embedmessage})",
                f"4\N{COMBINING ENCLOSING KEYCAP} Would you like to be DMed on message edits? (currently {editmessage})",
                f"5\N{COMBINING ENCLOSING KEYCAP} Would you like your keywords to get triggered by bots? (currently {bottrigger})",
                f"6\N{COMBINING ENCLOSING KEYCAP} Would you like to be DMed when a message you sent is replied to? (currently {replymessage})"
            ]
            await message.edit(content=("\n".join(new_options)))

        await ctx.send("Done!")
        await message.delete(delay=1.0)


def setup(bot):
    bot.add_cog(UserSettings(bot))
