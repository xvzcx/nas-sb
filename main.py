import discord
import asyncio
import os
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── SYSTEM PULSE (Keep-alive for Railway) ───
app = Flask(__name__)

@app.route('/')
def home():
    return "SYSTEM ONLINE"

def run_flask():
    # Railway provides the PORT environment variable.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ─── CONFIG ───
# Make sure "DISCORD_TOKEN" is in your Railway Variables tab!
TOKEN = os.getenv("DISCORD_TOKEN")

# ─── Bot Class ───
class Kill(commands.Bot):
    def __init__(self, display_name="Main"):
        # We removed intents entirely here to fix the AttributeError
        super().__init__(
            command_prefix="!",
            self_bot=True,
            help_command=None
        )
        self.display_name = display_name
        self.spamming = False

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.display_name} ({self.user}) ───")

    async def on_message(self, message):
        # Self-bot: Only listen to your own account
        if message.author.id != self.user.id:
            return
        await self.process_commands(message)

# ─── UI Helper ───
async def ui_send(ctx, title, body, color="34"):
    ui = (
        f"```ansi\n"
        f"[1;{color}m[ {title} ][0m\n"
        f"[1;30m────────────────────────────────[0m\n"
        f"{body}\n"
        f"[1;30m────────────────────────────────[0m\n"
        f"```"
    )
    await ctx.send(ui, delete_after=10)

# ─── Command Registration ───
def add_commands(bot: Kill):
    @bot.command()
    async def help(ctx):
        await ctx.message.delete()
        body = "!spam [n] [msg] | !purge [n]\n!stop"
        await ui_send(ctx, "COMMANDS", body, "35")

    @bot.command()
    async def spam(ctx, amount: int, *, text):
        await ctx.message.delete()
        bot.spamming = True
        for _ in range(amount):
            if not bot.spamming: break
            await ctx.send(text)
            await asyncio.sleep(0.8) 
        bot.spamming = False

    @bot.command()
    async def purge(ctx, amount: int):
        await ctx.message.delete()
        def is_me(m): return m.author.id == bot.user.id
        deleted = await ctx.channel.purge(limit=amount, check=is_me)
        await ui_send(ctx, "PURGE", f"Removed {len(deleted)} messages", "34")

    @bot.command()
    async def stop(ctx):
        await ctx.message.delete()
        bot.spamming = False
        await ui_send(ctx, "SYSTEM", "Operations Halted", "31")

# ─── Execution ───
if __name__ == "__main__":
    # 1. Start Flask in a background thread
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    # 2. Start the Bot
    if not TOKEN:
        print("CRITICAL: DISCORD_TOKEN is missing in Railway Variables.")
    else:
        master_bot = Kill()
        add_commands(master_bot)
        try:
            master_bot.run(TOKEN)
        except Exception as e:
            print(f"Connection Failed: {e}")
