import aiohttp
import discord
from discord.ext import commands
import voxelbotutils as utils


class LoggerAndHandler(utils.Cog, name="Logger And Handler"):

    @utils.Cog.listener()
    async def on_guild_join(self, guild):
        """Sends the name and membercount of every server the bot joins"""

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url('https://discordapp.com/api/webhooks/744353242322043001/V3WMdShI8L8LZLStNUBaqG2WI-qZrdofCQFM1QkW4oLTIcRA4TMC5ffKFpS2JyIXp96w', adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(f'StalkerBot was added to `{guild.name}` (`{guild.id}`). `{len([i for i in guild.members if not i.bot])}` members.', username='On Guild Join Event')

    @utils.Cog.listener()
    async def on_guild_remove(self, guild):
        """Sends the name and membercount of every server the bot leaves"""

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url('https://discordapp.com/api/webhooks/744353242322043001/V3WMdShI8L8LZLStNUBaqG2WI-qZrdofCQFM1QkW4oLTIcRA4TMC5ffKFpS2JyIXp96w', adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(f'StalkerBot was removed from `{guild.name}` (`{guild.id}`). `{len([i for i in guild.members if not i.bot])}` members.', username='On Guild Leave Event')

    @utils.command(aliases=['countservers'])
    @commands.is_owner()
    async def countguilds(self, ctx):
        """Counts how many guilds have the bot"""

        await ctx.send(f"The bot is in `{len(self.bot.guilds)}` guilds.")

    @utils.command()
    @commands.is_owner()
    async def countusers(self, ctx):
        """Counts how many unique user IDs there are"""

        async with self.bot.database() as db:
            distinctRows = await db("SELECT DISTINCT userid FROM keywords;")
            rows = await db("SELECT * FROM keywords;")

        await ctx.send(f"`{len(distinctRows)}` unique users have set up keywords and there are `{len(rows)}` keywords in total.")


def setup(bot):
    bot.add_cog(LoggerAndHandler(bot))
