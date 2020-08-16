import discord
from discord.ext import commands
#from discord import Webhook, AsyncWebhookAdapter

import aiohttp
import asyncpg
import io


class LoggerAndHandler(commands.Cog, name="Logger And Handler"):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url('https://discordapp.com/api/webhooks/744353242322043001/V3WMdShI8L8LZLStNUBaqG2WI-qZrdofCQFM1QkW4oLTIcRA4TMC5ffKFpS2JyIXp96w', adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(f'StalkerBot was added to `{guild.name}` (`{guild.id}`). `{len([i for i in guild.members if not i.bot])}` members.', username='On Guild Join Event')


    @commands.Cog.listener()
    async def on_guild_remove(self, guild):

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url('https://discordapp.com/api/webhooks/744353242322043001/V3WMdShI8L8LZLStNUBaqG2WI-qZrdofCQFM1QkW4oLTIcRA4TMC5ffKFpS2JyIXp96w', adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(f'StalkerBot was removed from `{guild.name}` (`{guild.id}`). `{len([i for i in guild.members if not i.bot])}` members.', username='On Guild Leave Event')

    @commands.command()
    async def countguilds(self, ctx):
        """Counts how many guilds have the bot"""

        await ctx.send(f"The bot is in `{len(self.bot.guilds)}` guilds.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        error.read().decode('utf-8')
        data = io.StringIO(error)
        data.seek(0)
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url('https://discordapp.com/api/webhooks/744353242322043001/V3WMdShI8L8LZLStNUBaqG2WI-qZrdofCQFM1QkW4oLTIcRA4TMC5ffKFpS2JyIXp96w', adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(file=discord.File(data, filename="error.py"))






def setup(bot):
    bot.add_cog(LoggerAndHandler(bot))
