from discord.ext import commands
import asyncpg


class PrefixCommands(commands.Cog, name="Prefix Commands"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['changeprefix'])
    async def prefix(self, ctx, prefix:str=None):
        """Changes the prefix of the server (or gives you set prefix)"""

        if ctx.guild is None:
            await ctx.send("This command does not work in DMs. Use the command on a server you have the `manage server` permission on.")

        if prefix is None:
            async with self.bot.database() as db:
                prefixRows = await db("SELECT * from prefix where guildid = $1", ctx.guild.id)
            
            await ctx.send(f"The prefix for this server is `{prefixRows[0]['prefix']}`")
            return

        if len(prefix) > 50:
            await ctx.send("Could not set that as a prefix as it is longer than 50 characters.")
            return
        if len(prefix) < 1:
            await ctx.send("Could not set that as a prefix as it is shorter than 1 character.")
            return

        if ctx.author.guild_permissions.manage_guild is False:
            await ctx.send("You don't have permission to run this command (You need the `manage server` permission)")
            return

        async with self.bot.database() as db:
            await db("INSERT into prefix (guildid, prefix) VALUES ($1, $2) on conflict (guildid) do update set prefix = $2", ctx.guild.id, prefix)

        await ctx.send(f"Set prefix to `{prefix}`")



def setup(bot):
    bot.add_cog(PrefixCommands(bot))
