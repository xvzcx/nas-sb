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
        # Toggling States
        self.spamming = False
        self.mock_target = None
        self.uwu_target = None
        self.react_target_id = None
        self.react_emojis = [] 
        # AFK System
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []
        # Profile & Status
        self.status_dot = discord.Status.online
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")
        print(f"─── PREFIX: , ───")

    async def force_status_update(self, text):
        """Standard discord.py CustomActivity can be flakey; this uses the state field."""
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.custom, name="Custom Status", state=text),
            status=self.status_dot
        )

    # ─── THE CORE ENGINE ───
    async def on_message(self, message):
        # 1. PROCESS YOUR COMMANDS
        if message.author.id == self.user.id:
            await self.process_commands(message)
            # AFK Auto-Disable
            if self.afk_reason and not message.content.startswith(self.command_prefix):
                if (time.time() - self.afk_time) > 3:
                    log_text = "\n".join(self.afk_log) if self.afk_log else "No pings received."
                    await ui_send(message.channel, "WELCOME BACK", f"Pings: {self.afk_pings}\n{log_text}", "AFK DISABLED", "32")
                    self.afk_reason, self.afk_pings, self.afk_log = None, 0, []
            return

        # 2. TARGETED AUTOMATIONS (OTHERS)
        if self.react_target_id and message.author.id == self.react_target_id:
            for emoji in self.react_emojis:
                try: 
                    await message.add_reaction(emoji.strip())
                    await asyncio.sleep(0.1) 
                except: pass

        if self.mock_target and message.author.id == self.mock_target:
            try: await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
            except: pass

        if self.uwu_target and message.author.id == self.uwu_target:
            try:
                uwu_content = message.content.replace('L','W').replace('R','W').replace('l','w').replace('r','w') + " uwu"
                await message.channel.send(uwu_content)
            except: pass

        # 3. AFK LOGGING
        if self.afk_reason and self.user.mentioned_in(message):
            self.afk_pings += 1
            self.afk_log.append(f"**{message.author}** in #{message.channel}")
            try: await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
            except: pass

bot = Kill()

# ─── UI ENGINE (THE FULL BOX) ───
async def ui_send(ctx, title, body, footer="Selfbot v2.6", color="34"):
    ui_box = (
        f"```ansi\n"
        f"[1;{color}m┏━━━━━━━ [ {title} ] ━━━━━━━┓[0m\n"
        f"{body}\n"
        f"[1;30m┗━━ {footer} ━━┛[0m\n"
        f"```"
    )
    target = ctx.channel if hasattr(ctx, 'channel') else ctx
    try: await target.send(ui_box, delete_after=8)
    except: await target.send(f"**[{title}]** {body}")

# ─── COMMANDS: PROFILE & RPC ───
@bot.command()
async def addstatus(ctx, *, text):
    bot.status_messages.append(text)
    await ui_send(ctx, "STATUS", f"Added: {text}\nTotal: {len(bot.status_messages)}", "SAVED", "35")

@bot.command()
async def rotatestatus(ctx, toggle):
    if toggle.lower() == "on":
        bot.rotating_status = True
        async def status_rotator():
            while bot.rotating_status:
                for text in bot.status_messages:
                    if not bot.rotating_status: break
                    await bot.force_status_update(text)
                    await asyncio.sleep(12)
        bot.loop.create_task(status_rotator())
        await ui_send(ctx, "STATUS", "Rotation: ON", "ACTIVE", "32")
    else:
        bot.rotating_status = False
        await ui_send(ctx, "STATUS", "Rotation: OFF", "STOPPED", "31")

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []
    bot.rotating_status = False
    await ui_send(ctx, "STATUS", "Wiped all statuses.", "CLEARED", "31")

@bot.command()
async def rpc(ctx, *, text):
    await bot.change_presence(activity=discord.Game(name=text), status=bot.status_dot)
    await ui_send(ctx, "RPC", f"Playing: {text}", "RICH PRESENCE", "34")

@bot.command()
async def dot(ctx, mode):
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    bot.status_dot = modes.get(mode.lower(), discord.Status.online)
    await bot.change_presence(status=bot.status_dot)
    await ui_send(ctx, "DOT", f"Status: {mode.upper()}", "UPDATED", "34")

@bot.command()
async def addbio(ctx, *, text):
    bot.bio_messages.append(text)
    await ui_send(ctx, "BIO", f"Added: {text}", "SAVED", "32")

@bot.command()
async def rotatebio(ctx, toggle):
    if toggle.lower() == "on":
        bot.rotating_bio = True
        async def bio_rotator():
            while bot.rotating_bio:
                for text in bot.bio_messages:
                    if not bot.rotating_bio: break
                    requests.patch("https://discord.com/api/v9/users/@me", headers={"Authorization": os.getenv("DISCORD_TOKEN")}, json={"bio": text})
                    await asyncio.sleep(45)
        bot.loop.create_task(bio_rotator())
        await ui_send(ctx, "BIO", "Rotation: ON", "ACTIVE", "32")
    else:
        bot.rotating_bio = False
        await ui_send(ctx, "BIO", "Rotation: OFF", "STOPPED", "31")

# ─── COMMANDS: TROLLING ───
@bot.command()
async def multireact(ctx, *, args):
    try:
        user_id = int(re.search(r'\d+', args).group())
        emoji_list = re.sub(r'<@!?\d+>', '', args).strip().split()
        bot.react_target_id = user_id
        bot.react_emojis = emoji_list[:3]
        await ui_send(ctx, "AUTO-REACT", f"Target: {user_id}\nEmojis: {' '.join(bot.react_emojis)}", "LOCKED", "36")
    except:
        await ui_send(ctx, "ERROR", "Usage: ,multireact @user 🔥 💀", "FAIL", "31")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    await ui_send(ctx, "AUTO-REACT", "Disabled.", "OFF", "31")

@bot.command()
async def mock(ctx, *, args):
    id_match = re.search(r'\d+', args)
    if id_match:
        bot.mock_target = int(id_match.group())
        bot.uwu_target = None
        await ui_send(ctx, "MOCK", f"Targeting: {bot.mock_target}", "ACTIVE", "31")

@bot.command()
async def uwu(ctx, *, args):
    id_match = re.search(r'\d+', args)
    if id_match:
        bot.uwu_target = int(id_match.group())
        bot.mock_target = None
        await ui_send(ctx, "UWU", f"Targeting: {bot.uwu_target}", "ACTIVE", "35")

@bot.command()
async def unmock(ctx):
    bot.mock_target = bot.uwu_target = None
    await ui_send(ctx, "TROLL", "Mock/UwU disabled.", "OFF", "31")

# ─── COMMANDS: UTILITY ───
@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(text)
        await asyncio.sleep(1.1)

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    count = 0
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: 
                await msg.delete()
                count += 1
                await asyncio.sleep(0.1)
            except: pass
    await ui_send(ctx, "PURGE", f"Deleted {count} messages.", "SUCCESS", "34")

@bot.command()
async def afk(ctx, *, reason="Away"):
    bot.afk_reason, bot.afk_time = reason, time.time()
    await ui_send(ctx, "AFK", f"Reason: {reason}", "SET", "33")

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = bot.mock_target = bot.uwu_target = None
    await bot.change_presence(activity=None)
    await ui_send(ctx, "STOP", "All background tasks halted.", "CLEAN", "31")

@bot.command()
async def ping(ctx):
    await ui_send(ctx, "PONG", f"Latency: {round(bot.latency * 1000)}ms", "ACTIVE", "32")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
