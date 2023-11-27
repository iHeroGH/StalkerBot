import io

import discord
from discord.ext import commands, vbu

class ModerationCommands(vbu.Cog, name="Moderation Commands"):

    def __init__(self, bot):
        self.bot = bot

    @vbu.command()
    @commands.is_owner()
    async def listall(self, ctx, user:discord.User=None):
        """Lists either a user's entire list of keywords or the entire database"""

        async with vbu.Database() as db:
            if user:
                full = await db("SELECT * FROM keywords WHERE userid = $1;", user.id)
            else:
                full = await db("SELECT * FROM keywords;")

        text = []
        for x in full:
            user = self.bot.get_user(x['userid']) or await self.bot.fetch_user(x['userid'])
            text.append(f"User: {user.name}({user.id}) - Keyword: {x['keyword']}")
        text = "\n".join(sorted(text)) + "\n"
        await ctx.send(file=discord.File(io.StringIO(text), filename="AllUsers.txt"))

    @vbu.command()
    @commands.is_owner()
    async def forceremove(self, ctx, user:discord.User, keyword:str):
        """Forcibly removes a keyword from a user"""

        async with vbu.Database() as db:
            await db("DELETE FROM keywords WHERE userid = $1 AND keyword = $2;", user.id, keyword)

        await ctx.send(f"Removed `{keyword}` from {user.name}'s list")

    @vbu.command()
    @commands.is_owner()
    async def forceadd(self, ctx, user:discord.User, keyword:str):
        """Forcibly adds a keyword to a user"""

        async with vbu.Database() as db:
            await db("INSERT INTO keywords VALUES ($1, $2);", user.id, keyword)
        await ctx.send(f"Added `{keyword}` to {user.name}'s list")


def setup(bot):
    bot.add_cog(ModerationCommands(bot))
