import discord
from discord.ext import commands
import json

with open("config.json") as a:
    config = json.load(a)

bot_token = config["token"]
database_auth = config["database"]    

bot = commands.Bot(command_prefix=commands.when_mentioned_or("s."))
bot.database_auth = database_auth

bot.load_extension("cogs.BotCommands")
bot.load_extension("cogs.PrefixCommands")
bot.load_extension("jishaku")
bot.run(bot_token)
