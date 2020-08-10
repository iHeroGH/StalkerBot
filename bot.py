import discord
from discord.ext import commands
import json
import asyncpg

with open("config.json") as a:
    config = json.load(a)

bot_token = config["token"]
database_auth = config["database"]    

async def getprefix(bot, message):
    """Actually changes the prefix it looks for"""
    if message.guild is None:
        return commands.when_mentioned_or("s.")(bot,message)

    connection = await asyncpg.connect(**database_auth)
    prefixRows = await connection.fetch("SELECT from prefix where guildid = $1", message.guild.id)
    await connection.close()

    try:
        prefix = prefixRows[0]['prefix']
    except IndexError:
        prefix = "s."
    return commands.when_mentioned_or(prefix)(bot,message)

bot = commands.Bot(command_prefix=getprefix)
bot.database_auth = database_auth

bot.load_extension("cogs.BotCommands")
bot.load_extension("cogs.PrefixCommands")
bot.load_extension("jishaku")
bot.run(bot_token)
