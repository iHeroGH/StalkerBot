async def containsStalkerTrigger(self, message):
    content = message.content.lower()
        if content.index("stalker").first():
            if content.index("reklats").first():
                if content.index("stalker").first() > content.index("reklats").first():
                    await message.add_reaction("👀")
                    await message.add_reaction("<:backwards_eyes:785981504127107112>")
                else:
                    await message.add_reaction("<:backwards_eyes:785981504127107112>")
                    await message.add_reaction("👀")
            else:
                await message.add_reaction("👀")
        elif content.index("reklats").first():
            await message.add_reaction("<:backwards_eyes:785981504127107112>")
