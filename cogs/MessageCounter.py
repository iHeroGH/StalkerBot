from discord.ext import tasks, commands

class MessageCounter(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.counter = 0
        self.tell_me_more.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        self.bot.counter += 1

    @tasks.loop(minutes=10)
    async def tell_me_more(self):
        await self.bot.get_user(322542134546661388).send(f"Bot has received {self.bot.counter} messages over 10 minutes")
        self.bot.counter = 0


def setup(bot):
    bot.add_cog(MessageCounter(bot))
