import discord
import asyncio
import os
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── SYSTEM PULSE ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ─── CONFIG ───
TOKEN = os.getenv("DISCORD_TOKEN")

# ─── Bot Class ───
class Kill(commands.Bot):
    def __init__(self, display_name="Main"):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.display_name = display_name
        self.spamming = False
        # --- Auto-React Variables ---
        self.target_id = None
        self.react_emoji = None

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.display_name} ({self.user}) ───")

    async def on_message(self, message):
        # 1. Auto-React Logic (Triggers on others)
        if self.target_id and self.react_emoji:
            if message.author.id == self.target_id:
                try:
                    await message.add_reaction(self.react_emoji)
                except:
                    pass

        # 2. Command Logic (Only listen to you)
        if message.author.id != self.user.id:
            return
        await self.process_commands(message)

# ─── UI Helper ───
async def ui_send(ctx, title, body, color="34"):
    ui = (f"```ansi\n[1;{color}m[ {title} ][0m\n"
          f"[1;30m────────────────────────────────[0m\n"
          f"{body}\n"
          f"[1;30m────────────────────────────────[0m\n```")
    await ctx.send(ui, delete_after=5)

# ─── Command Registration ───
def add_commands(bot: Kill):
    @bot.command()
    async def help(ctx):
        await ctx.message.delete()
        body = ",spam [n] [msg] | ,purge [n]\n,react [id] [emoji] | ,stop"
        await ui_send(ctx, "COMMANDS", body, "35")

    @bot.command()
    async def react(ctx, user_id: int, emoji: str):
        await ctx.message.delete()
        bot.target_id = user_id
        bot.react_emoji = emoji
        await ui_send(ctx, "AUTO-REACT", f"Target: {user_id}\nEmoji: {emoji}", "32")

    @bot.command()
    async def spam(ctx, amount: int, *, text):
        await ctx.message.delete()
        bot.spamming = True
        for _ in range(amount):
            if not bot.spamming: break
            await ctx.send(text)
            await asyncio.sleep(0.4) 
        bot.spamming = False

    @bot.command()
    async def purge(ctx, amount: int):
        await ctx.message.delete()
        def is_me(m): return m.author.id == bot.user.id
        await ctx.channel.purge(limit=amount, check=is_me)
        await ui_send(ctx, "PURGE", f"Cleared {amount} messages", "34")

    @bot.command()
    async def stop(ctx):
        await ctx.message.delete()
        bot.spamming = False
        bot.target_id = None # Turns off auto-react
        bot.react_emoji = None
        await ui_send(ctx, "SYSTEM", "All Operations Halted", "31")

# ─── Execution ───
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    if TOKEN:
        master_bot = Kill()
        add_commands(master_bot)
        master_bot.run(TOKEN)
