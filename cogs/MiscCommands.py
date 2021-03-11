import discord
from discord.ext import commands

import typing
import aiohttp
import io
from PIL import Image
import voxelbotutils as utils

from converters import send_type, send_snowflake, reaction_channel


class MiscCommands(utils.Cog, name="Miscellaneous Commands"):

    STALKER_CHANNEL = 772615385102549022

    last_dm = 322542134546661388
    
    def __init__(self, bot):
        super().__init__(bot)

    @utils.Cog.listener()
    async def on_message(self, message):

        # If the message is in DMs, and it isn't a command, and it isn't sent by StalkerBot
        if message.guild is None and not message.content.lower().startswith("s.") and message.author.id != 723813550136754216:
            embed = discord.Embed()
            embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
            embed.set_footer(text=f"Author: {str(message.author)} ({message.author.id})\nChannel ID: {message.channel.id}\nMessage ID: {message.id}")
            if message.attachments:
                url_list = [i.url for i in message.attachments]
                lines = ""
                for i in url_list:
                    lines = lines + f"\n[Click Here]({i})"
                embed.add_field(name="Attatchment Links", value=lines, inline=False)
                embed.set_image(url=message.attachments[0].url)
            embed.description = message.content
            await self.bot.get_channel(self.STALKER_CHANNEL).send(embed=embed)

            self.last_dm = message.author.id

    @utils.command(aliases=['dmbl'], hidden=True)
    @commands.is_owner()
    async def dmblacklist(self, ctx, user:discord.User=None):
        """Blacklists a user from being detected by the DM Stalker"""
        user = user or self.bot.get_user(self.last_dm)

        async with self.bot.database() as db:
            current_bl = await db("SELECT * FROM dm_blacklist")
            if current_bl:
                await db("DELETE * FROM dm_blacklist WHERE user_id = $1", user.id)
                await ctx.send(f"Removed {user.mention} ({str(user)}) from the DM blacklist.", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))
            else:
                await db("INSERT INTO dm_blacklist (user_id) VALUES ($1)", user.id)
                await ctx.send(f"Inserted {user.mention} ({str(user)}) into the DM blacklist.", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @utils.command(aliases=['hero', 'h'], hidden=True)
    @commands.bot_has_permissions(attach_files=True)
    async def heroify(self, ctx, ident='h', url:typing.Union[discord.User or discord.ClientUser, str]=None):

        possible = ['h', 'H', 'A', 'a', 'm', 'L', 'l', 'e', 'V']
        if ident not in possible:
            return await ctx.send(f"You didn't provide a valid heroify identifier ({', '.join(possible)})")

        # Decide what type of H to use
        h_type = {
            "h": 'images/cursive_hero_h.png',  # Cursive H
            "H": 'images/hero_h.png',  # Normal H
            "A": 'images/aiko_a.png',  # Aiko A
            "a": 'images/cursive_aiko_a.png', # Cursive A
            "m": 'images/megan_m.png', # Megan M
            "L": 'images/liz_l.png',  # Liz L
            "l": 'images/lemon.png',  # Lemon
            "e": 'images/eyes.png', # Eyes
            "V": 'images/vt_v.png' # Vibe Talk V
        }[ident[0]]

        # Check if the image should be a user PFP
        if isinstance(url, discord.User):
            url = str(url.avatar_url_as(format="png"))

        # Set the image URL to the message attachment link if it's None
        if url is None:
            if len(ctx.message.attachments) > 0:
                url = ctx.message.attachments[0].url
            else:
                return await ctx.send("You didn't provide a valid image URL")

        # Get the data from the url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                image_bytes = await r.read()

        # "Hey python, treat this as a file so you can open it later"
        image_file = io.BytesIO(image_bytes)

        # Assign variables for the images (the image sent by user and the H)
        base_image = Image.open(image_file)
        h_image = Image.open(h_type)

        # Resize the base image to be the same size as the H
        base_image = base_image.resize(h_image.size)

        # Add an H to the base image
        base_image.paste(h_image, (0, 0), h_image)

        # Change the base image back to bytes so we can send it to Discord
        sendable_image = io.BytesIO()
        base_image.save(sendable_image, "PNG")
        sendable_image.seek(0)

        await ctx.send(file=discord.File(sendable_image, filename="heroed.png"))

    @utils.command()
    @commands.is_owner()
    async def send(self, ctx, channel_type:send_type.SendType, snowflake:typing.Optional[send_snowflake.SendSnowflake], *, message:str=None):
        """Sends a message to a channel or a user through StalkerBot"""

        print(channel_type, snowflake, message)
        # Set the user to whoever last DMed stalkerbot
        if channel_type == "u":
            snowflake = snowflake or self.bot.get_user(self.last_dm)

        snowflake = snowflake or ctx.channel
        # Hopefully `snowflake` is a Discord object, but if it's an int we should try getting it
        if type(snowflake) is int:
            method = {
                "c": self.bot.get_channel,
                "u": self.bot.get_user,
            }[channel_type[0]]
            snowflake = method(snowflake)

        # Set up what we want to send
        payload = {
            "content": message,
        }

        # Different send if the message had attachments
        if ctx.message.attachments:
            async with aiohttp.ClientSession() as session:
                async with session.get(ctx.message.attachments[0].url) as r:
                    image_bytes = await r.read()
            image_file = io.BytesIO(image_bytes)
            payload["file"] = discord.File(image_file, filename="image.png")

        # And send
        print(f"Sending {snowflake} message {payload['content']}")
        await snowflake.send(**payload)

        # React to (or delete) the command message
        if snowflake == ctx.channel:
            await ctx.message.delete()
        else:
            await ctx.message.add_reaction("👌")

    @utils.command()
    @commands.is_owner()
    async def react(self, ctx, message:discord.Message, *reactions):
        """Reacts to a message in a channel with a reaction"""

        # Default reaction to okay if none are provided
        if not reactions:
            reactions = ['okay']

        for reaction in reactions: # Loop through the reactions
            try:
                reaction = {  # Preset reactions
                    "ok": ["👌"],
                    "okay": ["👌"],
                    "up": ["👍"],
                    "down": ["👎"],
                    "hearts": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍"]
                }[reaction.lower()]
            except KeyError: # if it isn't in the presets, it's itself
                reaction = [reaction]

            # Go through the reactions
            for r in reaction:
                await message.add_reaction(r)
                
        
        await ctx.message.add_reaction("👌") # React to the command with a confirmation


def setup(bot):
    bot.remove_command("send")
    bot.add_cog(MiscCommands(bot))
