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

class Kill(commands.Bot):
    def __init__(self, display_name="Main"):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.spamming = False
        self.target_id = None
        self.react_emoji = None
        self.afk_reason = None
        self.afk_time = 0
        self.rotating_status = False
        self.status_messages = []
        self.status_dot = discord.Status.online
        self.dm_running = False

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    async def status_rotator(self):
        while self.rotating_status:
            if not self.status_messages: break
            for text in self.status_messages:
                if not self.rotating_status: break
                await self.change_presence(
                    activity=discord.CustomActivity(name=text),
                    status=self.status_dot
                )
                await asyncio.sleep(5)

    async def on_message(self, message):
        # 1. AFK Responder
        if self.afk_reason and self.user.mentioned_in(message) and message.author.id != self.user.id:
            try:
                await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
                return 
            except: pass

        # 2. Auto-React
        if self.target_id and self.react_emoji and message.author.id == self.target_id:
            try: await message.add_reaction(self.react_emoji)
            except: pass
        
        # 3. Self-Command / AFK Clear Logic
        if message.author.id == self.user.id:
            if message.content.startswith("**[AFK]**"): return
            if message.content.startswith(self.command_prefix):
                await self.process_commands(message)
                return
            if self.afk_reason:
                if (time.time() - self.afk_time) < 2: return
                self.afk_reason = None
                await ui_send(message.channel, "SYSTEM", "Welcome back! AFK removed.", "32")

# ─── UI Helper ───
async def ui_send(ctx, title, body, footer="Selfbot", color="34"):
    ui = (f"```ansi\n"
          f"[1;{color}m┏━━━━━━ [ {title} ] ━━━━━━┓[0m\n"
          f"{body}\n"
          f"[1;30m┗━━ {footer} ━━┛[0m\n```")
    dest = ctx.channel if hasattr(ctx, 'channel') else ctx
    await dest.send(ui, delete_after=15)

# ─── Command Registration ───
def add_commands(bot: Kill):
    
    @bot.command()
    async def help(ctx, category: str = None):
        if category is None:
            title = "HELP MENU"
            body = ("[1;34m,help utility[0m - Tools & AFK\n"
                    "[1;35m,help status[0m  - RPC & Dot\n"
                    "[1;31m,help social[0m  - DMs & React")
            footer = "Type a category name"
            color = "37"
        elif category.lower() == "utility":
            title = "UTILITY CMDS"
            body = ("[1;37m,afk [reason][0m - Set AFK\n"
                    "[1;37m,purge [n][0m    - Clear msgs\n"
                    "[1;37m,ping[0m         - Latency\n"
                    "[1;37m,stop[0m         - Kill all")
            footer = "Category: Utility"
            color = "34"
        elif category.lower() == "status":
            title = "STATUS CMDS"
            body = ("[1;37m,dot [color][0m  - online/dnd/etc\n"
                    "[1;37m,addmsg [tx][0m  - Add to list\n"
                    "[1;37m,rotate [on][0m  - Start text\n"
                    "[1;37m,rpc [text][0m   - Stream box")
            footer = "Category: Status"
            color = "35"
        elif category.lower() == "social":
            title = "SOCIAL CMDS"
            body = ("[1;37m,massdm [msg][0m - DM friends\n"
                    "[1;37m,stopdm[0m       - Stop DMs\n"
                    "[1;37m,react [@u][0m   - Auto-emoji\n"
                    "[1;37m,spam [n] [t][0m - Message spam")
            footer = "Category: Social"
            color = "31"
        else: return await ui_send(ctx, "ERROR", "Invalid Category", "!", "31")
        await ui_send(ctx, title, body, footer, color)

    @bot.command()
    async def ping(ctx):
        ms = round(bot.latency * 1000)
        await ui_send(ctx, "PONG", f"Latency: [1;32m{ms}ms[0m", "Active", "32")

    @bot.command()
    async def afk(ctx, *, reason="I'm away."):
        bot.afk_reason = reason
        bot.afk_time = time.time()
        await ui_send(ctx, "AFK", f"Status: {reason}", "AFK SET", "33")

    @bot.command()
    async def purge(ctx, amount: int):
        await ctx.channel.purge(limit=amount, check=lambda m: m.author.id == bot.user.id)
        await ui_send(ctx, "PURGE", f"Cleared {amount}", "SUCCESS", "34")

    @bot.command()
    async def rpc(ctx, *, text: str):
        await bot.change_presence(activity=discord.Streaming(name=text, url="https://twitch.tv/discord"), status=bot.status_dot)
        await ui_send(ctx, "RPC", f"Streaming: {text}", "RPC SET", "35")

    @bot.command()
    async def addmsg(ctx, *, text: str):
        bot.status_messages.append(text)
        await ui_send(ctx, "STATUS", f"Added: {text}", "ROTATOR", "32")

    @bot.command()
    async def rotate(ctx, toggle: str):
        if toggle.lower() == "on":
            bot.rotating_status = True
            bot.loop.create_task(bot.status_rotator())
            await ui_send(ctx, "ROTATOR", "ENABLED", "ON", "32")
        else:
            bot.rotating_status = False
            await ui_send(ctx, "ROTATOR", "DISABLED", "OFF", "31")

    @bot.command()
    async def dot(ctx, mode: str):
        modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "inv": discord.Status.invisible}
        bot.status_dot = modes.get(mode.lower(), discord.Status.online)
        await bot.change_presence(status=bot.status_dot)
        await ui_send(ctx, "DOT", f"Mode: {mode.upper()}", "UPDATED", "34")

    @bot.command()
    async def massdm(ctx, *, message: str):
        bot.dm_running = True
        await ui_send(ctx, "MASS DM", "Starting DM Loop...", "RUNNING", "33")
        for friend in bot.user.friends:
            if not bot.dm_running: break
            try:
                await friend.send(message)
                await asyncio.sleep(5)
            except: pass
        bot.dm_running = False
        await ui_send(ctx, "MASS DM", "Finished.", "DONE", "32")

    @bot.command()
    async def spam(ctx, amount: int, *, text: str):
        bot.spamming = True
        for _ in range(amount):
            if not bot.spamming: break
            await ctx.send(text)
            await asyncio.sleep(0.5)
        bot.spamming = False

    @bot.command()
    async def react(ctx, target: str, emoji: str):
        bot.target_id = int(re.search(r'\d+', target).group())
        bot.react_emoji = emoji
        await ui_send(ctx, "REACT", f"Target: {bot.target_id}", "LOCKED", "32")

    @bot.command()
    async def stop(ctx):
        bot.dm_running = bot.rotating_status = bot.spamming = False
        bot.target_id = bot.afk_reason = None
        await bot.change_presence(activity=None)
        await ui_send(ctx, "SYSTEM", "All Tasks Killed.", "HALT", "31")

# ─── Execution ───
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    if TOKEN:
        master_bot = Kill()
        add_commands(master_bot)
        master_bot.run(TOKEN)
