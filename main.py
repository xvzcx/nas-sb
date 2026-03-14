import discord
import asyncio
import os
import re
import time
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
        self.afk_reason = None
        self.afk_time = 0 

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.display_name} ({self.user}) ───")

    async def on_message(self, message):
        if self.afk_reason and self.user.mentioned_in(message) and message.author.id != self.user.id:
            try:
                await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
                return 
            except: pass

        if self.target_id and self.react_emoji and message.author.id == self.target_id:
            try: await message.add_reaction(self.react_emoji)
            except: pass
        
        if message.author.id == self.user.id:
            if message.content.startswith("**[AFK]**"):
                return
            if message.content.startswith(self.command_prefix):
                await self.process_commands(message)
                return
            if self.afk_reason:
                if (time.time() - self.afk_time) < 2:
                    return
                self.afk_reason = None
                await ui_send(message.channel, "SYSTEM", "Welcome back! AFK removed.", "32")

# ─── UI Helper ───
async def ui_send(ctx, title, body, color="34"):
    ui = (f"```ansi\n[1;{color}m[ {title} ][0m\n"
          f"[1;30m────────────────────────────────[0m\n"
          f"{body}\n"
          f"[1;30m────────────────────────────────[0m\n```")
    dest = ctx.channel if hasattr(ctx, 'channel') else ctx
    await dest.send(ui, delete_after=5)

# ─── Command Registration ───
def add_commands(bot: Kill):
    @bot.command()
    async def help(ctx):
        body = (",spam [n] [msg] | ,purge [n]\n"
                ",react [@user] [emoji] | ,sr\n"
                ",afk [reason] | ,rpc [type] [text]\n"
                ",stop (all)")
        await ui_send(ctx, "COMMANDS", body, "35")

    @bot.command()
    async def rpc(ctx, activity_type: str, *, text: str = None):
        activity_type = activity_type.lower()
        
        if activity_type == "clear":
            await bot.change_presence(activity=None)
            await ui_send(ctx, "RPC", "Presence cleared.", "31")
            return

        if not text:
            await ui_send(ctx, "ERROR", "Usage: ,rpc [playing/streaming/watching] [text]", "31")
            return

        if activity_type == "playing":
            act = discord.Game(name=text)
        elif activity_type == "streaming":
            # Note: Streaming requires a valid Twitch/YouTube URL to show the purple icon
            act = discord.Streaming(name=text, url="https://www.twitch.tv/discord")
        elif activity_type == "watching":
            act = discord.Activity(type=discord.ActivityType.watching, name=text)
        elif activity_type == "listening":
            act = discord.Activity(type=discord.ActivityType.listening, name=text)
        else:
            await ui_send(ctx, "ERROR", "Types: playing, streaming, watching, listening, clear", "31")
            return

        await bot.change_presence(activity=act)
        await ui_send(ctx, "RPC", f"Status set to: {activity_type.title()} {text}", "32")

    @bot.command()
    async def afk(ctx, *, reason="I'm away right now."):
        bot.afk_reason = reason
        bot.afk_time = time.time() 
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
