import discord
from discord.ext import commands, vbu

class PrivacyCommands(vbu.Cog, name="Privacy Commands"):

    def __init__(self, bot):
        self.bot = bot

    @vbu.command(aliases=['privacypolicy', 'policy'])
    async def privacy(self, ctx: vbu.Context):
        """Sends the public privacy policy of the bot"""

        privacy_policy = """
        While the name of the bot may be slightly misleading, StalkerBot is dedicated to keeping users' privacy safe:
        StalkerBot never saves your messages outside of Discord.
        StalkerBot only sends messages to other users if a keyword is said in those messages (or if the message is a reply).
        StalkerBot can access messages sent to it in DMs. (Message Hero#2313 to be removed from the DM list - this will not affect your keywords)
        This is to be able to provide bot support at ease to the user.

        Note: Opting out and then opting back in will remove you from the DM list and place you back into the rest of the features.

        To opt-out of triggering keywords, recieving keywords, and triggering the StalkerBot DM check, run the `/optout` command.
        To opt back in, run the `s.optin` command
        All users are opted in by default.
        """

        await ctx.author.send(privacy_policy)

    @vbu.command()
    async def optout(self, ctx: vbu.Context):
        """Opt-out of StalkerBot features"""

        async with vbu.Database() as db:
            current_opt = await db("SELECT * FROM user_opt WHERE user_id = $1", ctx.author.id)
            current_bl = await db("SELECT * FROM dm_blacklist WHERE user_id = $1", ctx.author.id)
            if not current_opt:
                await db("INSERT INTO user_opt (user_id) VALUES ($1)", ctx.author.id)
            if not current_bl:
                 await db("INSERT INTO dm_blacklist (user_id) VALUES ($1)", ctx.author.id)

        await ctx.send(f"Successfully opted-out of StalkerBot features.")

    @vbu.command()
    async def optin(self, ctx: vbu.Context):
        """Opt-in to StalkerBot features"""

        async with vbu.Database() as db:
            current_opt = await db("SELECT * FROM user_opt WHERE user_id = $1", ctx.author.id)
            #current_bl = await db("SELECT * FROM dm_blacklist WHERE user_id = $1", ctx.author.id)
            if current_opt:
                await db("DELETE FROM user_opt WHERE user_id = $1", ctx.author.id)
            # if current_bl:
            #      await db("DELETE FROM dm_blacklist WHERE user_id = $1", ctx.author.id)

        await ctx.send(f"Successfully opted-in to StalkerBot features.")


def setup(bot):
    bot.add_cog(PrivacyCommands(bot))
