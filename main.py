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
        # States
        self.spamming = False
        self.mock_target = None
        self.uwu_target = None
        self.react_target_id = None
        self.react_emojis = [] 
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []
        self.status_dot = discord.Status.online
        # Profile Rotation
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []

    async def on_ready(self):
        print(f"─── {self.user} | ALL SYSTEMS COMPOSITED ───")

    async def force_status(self, text):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name="Custom Status", state=text), status=self.status_dot)

    async def on_message(self, message):
        if message.author.id == self.user.id:
            await self.process_commands(message)
            # AFK Auto-Disable
            if self.afk_reason and not message.content.startswith(self.command_prefix):
                if (time.time() - self.afk_time) > 5:
                    log = "\n".join(self.afk_log) if self.afk_log else "No pings."
                    await ui_send(message.channel, "WELCOME BACK", f"Pings: {self.afk_pings}\n{log}", "AFK OFF", "32")
                    self.afk_reason, self.afk_pings, self.afk_log = None, 0, []
            return

        # --- AUTOMATIONS ---
        if self.react_target_id == message.author.id:
            for e in self.react_emojis:
                try: await message.add_reaction(e.strip())
                except: pass

        if self.mock_target == message.author.id:
            await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
        
        if self.uwu_target == message.author.id:
            await message.channel.send(message.content.replace('L','W').replace('R','W').replace('l','w').replace('r','w') + " uwu")

        if self.afk_reason and self.user.mentioned_in(message):
            self.afk_pings += 1
            self.afk_log.append(f"**{message.author}** in #{message.channel}")
            await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)

bot = Kill()

# ─── UI ENGINE ───
async def ui_send(ctx, title, body, footer="Selfbot v3.5", color="34"):
    ui = f"```ansi\n[1;{color}m┏━━━━━ [ {title} ] ━━━━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    try: await ctx.send(ui, delete_after=8)
    except: await ctx.send(f"**[{title}]** {body}")

# ─── PROFILE ROTATION ───
@bot.command()
async def addstatus(ctx, *, t):
    bot.status_messages.append(t)
    await ui_send(ctx, "STATUS", f"Added: {t}", "SAVED", "35")

@bot.command()
async def rotatestatus(ctx, mode):
    bot.rotating_status = (mode.lower() == "on")
    if bot.rotating_status:
        async def s_loop():
            while bot.rotating_status:
                for s in bot.status_messages:
                    if not bot.rotating_status: break
                    await bot.force_status(s); await asyncio.sleep(15)
        bot.loop.create_task(s_loop())
    await ui_send(ctx, "STATUS", f"Rotation: {mode.upper()}", "RUNNING", "35")

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []; bot.rotating_status = False
    await ui_send(ctx, "STATUS", "Wiped list.", "CLEARED", "31")

@bot.command()
async def addbio(ctx, *, t):
    bot.bio_messages.append(t)
    await ui_send(ctx, "BIO", f"Added: {t}", "SAVED", "32")

@bot.command()
async def rotatebio(ctx, mode):
    bot.rotating_bio = (mode.lower() == "on")
    if bot.rotating_bio:
        async def b_loop():
            while bot.rotating_bio:
                for b in bot.bio_messages:
                    if not bot.rotating_bio: break
                    requests.patch("https://discord.com/api/v9/users/@me", headers={"Authorization": os.getenv("DISCORD_TOKEN")}, json={"bio": b})
                    await asyncio.sleep(45)
        bot.loop.create_task(b_loop())
    await ui_send(ctx, "BIO", f"Rotation: {mode.upper()}", "RUNNING", "32")

# ─── TROLLING & SOCIAL ───
@bot.command()
async def mock(ctx, *, args):
    id_m = re.search(r'\d{17,19}', args)
    if id_m: bot.mock_target = int(id_m.group()); bot.uwu_target = None
    await ui_send(ctx, "MOCK", f"Target: {bot.mock_target}", "ACTIVE", "31")

@bot.command()
async def uwu(ctx, *, args):
    id_m = re.search(r'\d{17,19}', args)
    if id_m: bot.uwu_target = int(id_m.group()); bot.mock_target = None
    await ui_send(ctx, "UWU", f"Target: {bot.uwu_target}", "ACTIVE", "35")

@bot.command()
async def unmock(ctx):
    bot.mock_target = bot.uwu_target = None
    await ui_send(ctx, "TROLL", "Mock/UwU Disabled", "OFF", "31")

@bot.command()
async def multireact(ctx, *, args):
    id_m = re.search(r'\d{17,19}', args)
    if id_m:
        bot.react_target_id = int(id_m.group())
        bot.react_emojis = re.sub(r'<@!?\d+>', '', args).strip().split()[:3]
        await ui_send(ctx, "MULTI-REACT", f"Target: {bot.react_target_id}", "LOCKED", "36")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    await ui_send(ctx, "REACT", "Auto-react Off", "OFF", "31")

# ─── UTILITY & RPC ───
@bot.command()
async def dot(ctx, mode):
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    bot.status_dot = modes.get(mode.lower(), discord.Status.online)
    await bot.change_presence(status=bot.status_dot)
    await ui_send(ctx, "STATUS", f"Dot set to: {mode}", "UPDATED", "34")

@bot.command()
async def rpc(ctx, *, text):
    await bot.change_presence(activity=discord.Game(name=text))
    await ui_send(ctx, "RPC", f"Playing: {text}", "RICH PRESENCE", "34")

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for i in range(n):
        if not bot.spamming: break
        await ctx.send(text); await asyncio.sleep(1.1)
    bot.spamming = False

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
