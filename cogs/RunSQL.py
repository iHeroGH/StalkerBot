import discord
from discord.ext import commands
import io

class RunSQL(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    async def runsql(self, ctx, *, sql:str):
        """Runs a line of SQL into the sparcli database"""

        # Get the data we asked for
        async with self.bot.database() as db:
            rows = await db(sql.format(guild=ctx.guild.id, author=ctx.author.id, channel=ctx.channel.id))
        if not rows:
            return await ctx.send("No content.")

        # Set up some metadata for us to format things nicely
        headers = list(rows[0].keys())
        column_widths = {i: len(i) for i in headers}
        lines = []

        # See how long our lines are
        for row in rows:
            for header in headers:
                column_widths[header] = max([column_widths[header], len(str(row[header]))])

        # Work out our rows
        for row in rows:
            working = ""
            for header in headers:
                working += format(str(row[header]), f" <{column_widths[header]}") + "|"
            lines.append(working[:-1])

        # Add on our headers
        header_working = ""
        spacer_working = ""
        for header in headers:
            header_working += format(header, f" <{column_widths[header]}") + "|"
            spacer_working += "-" * column_widths[header] + "|"
        lines.insert(0, spacer_working[:-1])
        lines.insert(0, header_working[:-1])

        # Send it out
        string_output = '\n'.join(lines)
        try:
            await ctx.send(f"```\n{string_output}```")
        except discord.HTTPException:
            file = discord.File(io.StringIO(string_output), filename="runsql.txt")
            await ctx.send(file=file)
    


def setup(bot):
    bot.add_cog(RunSQL(bot))
