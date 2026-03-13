import discord
import asyncio
import os
import re
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
        self.target_id = None
        self.react_emoji = None
        # --- AFK Variables ---
        self.afk_reason = None

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.display_name} ({self.user}) ───")

    async def on_message(self, message):
        # 1. AFK Auto-Responder
        if self.afk_reason and self.user.mentioned_in(message) and message.author.id != self.user.id:
            try:
                await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
            except:
                pass

        # 2. Auto-React Logic
        if self.target_id and self.react_emoji:
            if message.author.id == self.target_id:
                try:
                    await message.add_reaction(self.react_emoji)
                except:
                    pass
        
        # 3. Process Commands (Only from you)
        if message.author.id != self.user.id:
            return

        # 4. Auto-Disable AFK if you type anything
        if self.afk_reason:
            self.afk_reason = None
            await ui_send(message.channel, "SYSTEM", "Welcome back! AFK removed.", "32")

        await self.process_commands(message)

# ─── UI Helper ───
async def ui_send(ctx, title, body, color="34"):
    ui = (f"```ansi\n[1;{color}m[ {title} ][0m\n"
          f"[1;30m────────────────────────────────[0m\n"
          f"{body}\n"
          f"[1;30m────────────────────────────────[0m\n```")
    # Using ctx.channel.send if ctx is a channel (for the auto-welcome back)
    dest = ctx.channel if hasattr(ctx, 'channel') else ctx
    await dest.send(ui, delete_after=5)

# ─── Command Registration ───
def add_commands(bot: Kill):
    @bot.command()
    async def help(ctx):
        body = (",spam [n] [msg] | ,purge [n]\n"
                ",react [@user] [emoji] | ,sr\n"
                ",afk [reason]\n"
                ",stop (all)")
        await ui_send(ctx, "COMMANDS", body, "35")

    @bot.command()
    async def afk(ctx, *, reason="I'm away right now."):
        bot.afk_reason = reason
        await ui_send(ctx, "AFK", f"Status set: {reason}", "33")

    @bot.command()
    async def react(ctx, target: str, emoji: str):
        user_id_match = re.search(r'\d+', target)
        if user_id_match:
            bot.target_id = int(user_id_match.group())
            bot.react_emoji = emoji
            await ui_send(ctx, "AUTO-REACT", f"Targeting: {bot.target_id}", "32")

    @bot.command()
    async def sr(ctx):
        bot.target_id = None
        bot.react_emoji = None
        await ui_send(ctx, "AUTO-REACT", "Stopped reactions.", "31")

    @bot.command()
    async def spam(ctx, amount: int, *, text):
        bot.spamming = True
        for _ in range(amount):
            if not bot.spamming: break
            try:
                await ctx.send(text)
                await asyncio.sleep(0.4)
            except: break
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
        bot.afk_reason = None
        await ui_send(ctx, "SYSTEM", "Killed all tasks.", "31")

# ─── Execution ───
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    if TOKEN:
        master_bot = Kill()
        add_commands(master_bot)
        master_bot.run(TOKEN)
