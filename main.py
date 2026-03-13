# ─── Command Registration ───
def add_commands(bot: Kill):
    @bot.command()
    async def help(ctx):
        body = ",spam [n] [msg] | ,purge [n]\n,react [@user/id] [emoji]\n,sr (stop react) | ,stop (all)"
        await ui_send(ctx, "COMMANDS", body, "35")

    @bot.command()
    async def react(ctx, target: str, emoji: str):
        # This bit of "magic" allows you to either ping OR paste the ID
        user_id = "".join(filter(str.isdigit, target))
        if user_id:
            bot.target_id = int(user_id)
            bot.react_emoji = emoji
            await ui_send(ctx, "AUTO-REACT", f"Targeting: {user_id}\nEmoji: {emoji}", "32")
        else:
            await ui_send(ctx, "ERROR", "Invalid User or ID", "31")

    @bot.command()
    async def sr(ctx):
        bot.target_id = None
        bot.react_emoji = None
        await ui_send(ctx, "AUTO-REACT", "Stopped all reactions.", "31")

    @bot.command()
    async def spam(ctx, amount: int, *, text):
        bot.spamming = True
        for _ in range(amount):
            if not bot.spamming: break
            await ctx.send(text)
            await asyncio.sleep(0.4) 
        bot.spamming = False

    @bot.command()
    async def purge(ctx, amount: int):
        def is_me(m): return m.author.id == bot.user.id
        await ctx.channel.purge(limit=amount, check=is_me)
        await ui_send(ctx, "PURGE", f"Cleared {amount}", "34")

    @bot.command()
    async def stop(ctx):
        bot.spamming = False
        bot.target_id = None
        bot.react_emoji = None
        await ui_send(ctx, "SYSTEM", "Killed all tasks.", "31")
