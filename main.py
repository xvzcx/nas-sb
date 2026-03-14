import discord
import asyncio
import os
import re
import time
import random
import requests
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
        self.afk_pings = 0
        self.afk_log = []
        self.rotating_status = False
        self.status_messages = []
        self.status_dot = discord.Status.online
        self.dm_running = False
        self.mock_target = None
        self.uwu_target = None
        # Bio Rotator
        self.rotating_bio = False
        self.bio_messages = []

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    def update_bio(self, text):
        """Manually updates the 'About Me' section via API"""
        url = "https://discord.com/api/v9/users/@me/profile"
        headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
        data = {"bio": text}
        requests.patch(url, headers=headers, json=data)

    async def status_rotator(self):
        while self.rotating_status:
            if not self.status_messages: break
            for text in self.status_messages:
                if not self.rotating_status: break
                await self.change_presence(activity=discord.CustomActivity(name=text), status=self.status_dot)
                await asyncio.sleep(5)

    async def bio_rotator(self):
        while self.rotating_bio:
            if not self.bio_messages: break
            for text in self.bio_messages:
                if not self.rotating_bio: break
                self.update_bio(text)
                await asyncio.sleep(30) # Safe interval for Bio

    def sPoNgEbOb(self, text):
        return "".join([char.upper() if i % 2 == 0 else char.lower() for i, char in enumerate(text)])

    def uwuify(self, text):
        text = text.replace('L', 'W').replace('R', 'W').replace('l', 'w').replace('r', 'w')
        suffix = random.choice([" uwu", " owo", " >w<", " :3"])
        return text + suffix

    async def on_message(self, message):
        if message.author.id != self.user.id:
            if self.mock_target and message.author.id == self.mock_target:
                try: await message.channel.send(self.sPoNgEbOb(message.content))
                except: pass
            if self.uwu_target and message.author.id == self.uwu_target:
                try: await message.channel.send(self.uwuify(message.content))
                except: pass
            if self.afk_reason and self.user.mentioned_in(message):
                self.afk_pings += 1
                log_entry = f"**{message.author}** in #{message.channel}"
                if log_entry not in self.afk_log: self.afk_log.append(log_entry)
                try: await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
                except: pass
            if self.target_id and self.react_emoji and message.author.id == self.target_id:
                try: await message.add_reaction(self.react_emoji)
                except: pass
        
        if message.author.id == self.user.id:
            if message.content.startswith("**[AFK]**"): return
            if message.content.startswith(self.command_prefix):
                await self.process_commands(message)
                return
            if self.afk_reason:
                if (time.time() - self.afk_time) < 2: return
                log_text = "\n".join(self.afk_log) if self.afk_log else "No pings recorded."
                msg = f"Welcome back!\nPings: **{self.afk_pings}**\n[1;30mLogged:[0m\n{log_text}"
                self.afk_reason, self.afk_pings, self.afk_log = None, 0, []
                await ui_send(message.channel, "SYSTEM", msg, "AFK REMOVED", "32")

# ─── UI Helper ───
async def ui_send(ctx, title, body, footer="Selfbot", color="34"):
    ui = (f"```ansi\n[1;{color}m┏━━━━ [ {title} ] ━━━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```")
    dest = ctx.channel if hasattr(ctx, 'channel') else ctx
    await dest.send(ui, delete_after=7)

# ─── Command Registration ───
def add_commands(bot: Kill):
    @bot.command()
    async def help(ctx, category: str = None):
        if category is None:
            title, color = "HELP MENU", "37"
            body = "[1;34m,help utility[0m\n[1;35m,help status[0m\n[1;31m,help social[0m"
        elif category.lower() == "utility":
            title, color = "UTILITY CMDS", "34"
            body = "[1;37m,afk [r][0m | [1;37m,purge [n][0m\n[1;37m,ping[0m | [1;37m,stop[0m"
        elif category.lower() == "status":
            title, color = "STATUS CMDS", "35"
            body = "[1;37m,dot [c][0m | [1;37m,rpc [t][0m\n[1;37m,addmsg [t][0m | [1;37m,rotate [on][0m\n[1;37m,addbio [t][0m | [1;37m,rotatebio [on][0m"
        elif category.lower() == "social":
            title, color = "SOCIAL CMDS", "31"
            body = "[1;37m,mock [@u][0m | [1;37m,uwu [@u][0m\n[1;37m,unmock[0m | [1;37m,massdm [m][0m | [1;37m,spam [n] [t][0m"
        else: return
        await ui_send(ctx, title, body, f"Category: {category or 'Main'}", color)

    @bot.command()
    async def purge(ctx, n: int):
        await ctx.message.delete()
        async for message in ctx.channel.history(limit=n):
            if message.author.id == bot.user.id:
                try: await message.delete(); await asyncio.sleep(0.2)
                except: continue
        await ctx.send(f"```ansi\n[1;34m[ PURGE ][0m Cleared {n} messages.```", delete_after=2)

    @bot.command()
    async def spam(ctx, amount: int, *, text: str):
        bot
