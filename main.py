import discord
import asyncio
import os
import re
import time
import requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── SYSTEM PULSE ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ─── THE BOT CLASS ───
class Kill(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.spamming = False
        self.mock_target = None
        self.uwu_target = None
        self.react_target_id = None
        self.react_emojis = ["🔥"] # Default emoji for simple autoreact
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []
        self.status_dot = discord.Status.online
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    async def force_status_update(self, text):
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.custom, name="Custom Status", state=text),
            status=self.status_dot
        )

    async def on_message(self, message):
        if message.author.id == self.user.id:
            await self.process_commands(message)
            return

        # Sticky Auto-React Logic
        if self.react_target_id and message.author.id == self.react_target_id:
            for emoji in self.react_emojis:
                try: 
                    await message.add_reaction(emoji.strip())
                except: 
                    pass

        # Trolling Logic
        if self.mock_target and message.author.id == self.mock_target:
            try: await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
            except: pass

        if self.uwu_target and message.author.id == self.uwu_target:
            try: await message.channel.send(message.content.replace('r','w').replace('l','w') + " uwu")
            except: pass

bot = Kill()

async def ui_send(ctx, title, body, footer="Selfbot v4.1", color="34"):
    ui_box = f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    try: await ctx.send(ui_box, delete_after=10)
    except: await ctx.send(f"**[{title}]** {body}")

# ─── FIXED REACT COMMANDS ───

@bot.command()
async def autoreact(ctx, *, args):
    """Usage: ,autoreact @user (Uses default 🔥)"""
    id_m = re.search(r'\d+', args)
    if id_m:
        bot.react_target_id = int(id_m.group())
        bot.react_emojis = ["🔥"] 
        await ui_send(ctx, "AUTO-REACT", f"Sticky Target: {bot.react_target_id}", "LOCKED", "32")

@bot.command()
async def multireact(ctx, *, args):
    """Usage: ,multireact @user 🔥 💀 🤡"""
    try:
        user_id = int(re.search(r'\d+', args).group())
        emojis = re.sub(r'<@!?\d+>', '', args).strip().split()[:3]
        bot.react_target_id = user_id
        bot.react_emojis = emojis
        await ui_send(ctx, "MULTI-REACT", f"Locked: {user_id}\nEmojis: {' '.join(emojis)}", "ACTIVE", "36")
    except:
        await ui_send(ctx, "ERR", "Mention + Emojis", "FAIL", "31")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    await ui_send(ctx, "REACT", "All reactions stopped.", "OFF", "31")

# ─── TURBO UTILITY ───

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(text)
        await asyncio.sleep(0.4) 

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: 
                await msg.delete()
                await asyncio.sleep(0.05) 
            except: pass

# ─── HELP SYSTEM ───

@bot.command()
async def help(ctx, category=None):
    if not category:
        body = "[1;34m,help status[0m\n[1;35m,help social[0m\n[1;31m,help util[0m"
        return await ui_send(ctx, "HELP MENU", body, "Select Category", "37")
    
    cat = category.lower()
    if cat == "status":
        body = "`,addstatus` | `,rotatestatus` | `,clearstatus` | `,rpc` | `,dot`"
        await ui_send(ctx, "HELP: STATUS", body, "Profile Controls", "35")
    elif cat == "social":
        body = "`,mock @u` | `,uwu @u` | `,unmock`\n`,autoreact @u` | `,multireact @u [e]` | `,stopreact`"
        await ui_send(ctx, "HELP: SOCIAL", body, "Trolling Tools", "36")
    elif cat == "util":
        body = "`,spam [n] [t]` | `,purge [n]` | `,afk` | `,stop`"
        await ui_send(ctx, "HELP: UTILITY", body, "Power Tools", "31")

# ─── OTHER ESSENTIALS ───

@bot.command()
async def mock(ctx, *, args):
    id_m = re.search(r'\d+', args)
    if id_m: bot.mock_target = int(id_m.group()); await ui_send(ctx, "MOCK", f"Target: {bot.mock_target}", "ACTIVE", "31")

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = bot.mock_target = bot.uwu_target = None
    await ui_send(ctx, "STOP", "Everything halted.", "CLEAN", "31")

@bot.command()
async def ping(ctx):
    await ui_send(ctx, "PONG", f"{round(bot.latency * 1000)}ms", "ACTIVE", "32")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
