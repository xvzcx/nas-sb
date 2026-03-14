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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ─── THE BOT CLASS ───
class Kill(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.spamming = False
        self.afk_reason = None
        self.react_target_id = None
        self.react_emojis = [] 
        self.status_dot = discord.Status.online
        
        # Profile Rotation
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    def update_profile_bio(self, text):
        url = "https://discord.com/api/v9/users/@me"
        headers = {"Authorization": os.getenv("DISCORD_TOKEN"), "Content-Type": "application/json"}
        try: requests.patch(url, headers=headers, json={"bio": text})
        except: pass

    async def bio_rotator(self):
        while self.rotating_bio:
            for text in self.bio_messages:
                if not self.rotating_bio: break
                self.update_profile_bio(text)
                await asyncio.sleep(45)

    async def status_rotator(self):
        while self.rotating_status:
            for text in self.status_messages:
                if not self.rotating_status: break
                try:
                    await self.change_presence(activity=discord.CustomActivity(name=text), status=self.status_dot)
                except: pass
                await asyncio.sleep(12)

    async def on_message(self, message):
        # CRITICAL: Always process commands first
        if message.author.id == self.user.id:
            await self.process_commands(message)

        # ─── AUTO-REACT ───
        if self.react_target_id and message.author.id == self.react_target_id:
            for emoji in self.react_emojis:
                try: 
                    await message.add_reaction(emoji.strip())
                    await asyncio.sleep(0.05) 
                except: pass

# ─── UI HELPER ───
async def ui_send(ctx, title, body, footer="Selfbot", color="34"):
    ui = f"```ansi\n[1;{color}m┏━━━━ [ {title} ] ━━━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    target = ctx.channel if hasattr(ctx, 'channel') else ctx
    await target.send(ui, delete_after=7)

bot = Kill()

# ─── STATUS COMMANDS ───
@bot.command()
async def addstatus(ctx, *, text: str):
    bot.status_messages.append(text)
    await ui_send(ctx, "STATUS", f"Added: {text}\nTotal: {len(bot.status_messages)}", "SAVED", "35")

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []
    bot.rotating_status = False
    await ui_send(ctx, "STATUS", "Status list wiped.", "CLEARED", "31")

@bot.command()
async def rotatestatus(ctx, toggle: str):
    if toggle.lower() == "on":
        if not bot.status_messages: return await ui_send(ctx, "FAIL", "Add statuses first.", "ERROR", "31")
        bot.rotating_status = True
        bot.loop.create_task(bot.status_rotator())
        await ui_send(ctx, "STATUS", "Turbo Status: **ON**", "12s DELAY", "35")
    else:
        bot.rotating_status = False
        await ui_send(ctx, "STATUS", "Rotation: **OFF**", "STOPPED", "31")

# ─── BIO COMMANDS ───
@bot.command()
async def addbio(ctx, *, text: str):
    bot.bio_messages.append(text)
    await ui_send(ctx, "BIO", f"Added: {text}", "SAVED", "32")

@bot.command()
async def clearbio(ctx):
    bot.bio_messages = []
    bot.rotating_bio = False
    await ui_send(ctx, "BIO", "Bio list wiped.", "CLEARED", "31")

@bot.command()
async def rotatebio(ctx, toggle: str):
    if toggle.lower() == "on":
        bot.rotating_bio = True
        bot.loop.create_task(bot.bio_rotator())
        await ui_send(ctx, "BIO", "Rotation: ON", "32")
    else:
        bot.rotating_bio = False
        await ui_send(ctx, "BIO", "Rotation: OFF", "31")

# ─── SOCIAL COMMANDS ───
@bot.command()
async def multireact(ctx, *, args: str):
    try:
        user_id = int(re.search(r'\d+', args).group())
        emoji_raw = re.sub(r'<@!?\d+>', '', args).strip()
        customs = re.findall(r'<a?:\w+:\d+>', emoji_raw)
        unicodes = [c for c in emoji_raw.split() if not c.startswith('<')]
        bot.react_target_id = user_id
        bot.react_emojis = (customs + unicodes)[:3]
        await ui_send(ctx, "MULTI-REACT", f"Target: {user_id}\nEmojis: {' '.join(bot.react_emojis)}", "LOCKED", "32")
    except:
        await ui_send(ctx, "ERROR", "Usage: ,multireact @user 🔥 💀", "FAIL", "31")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    bot.react_emojis = []
    await ui_send(ctx, "SOCIAL", "Auto-react disabled.", "OFF", "31")

# ─── UTILITY COMMANDS ───
@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    count = 0
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: 
                await msg.delete()
                count += 1
                await asyncio.sleep(0.08)
            except: pass
    await ctx.send(f"```ansi\n[1;34m[ PURGE ][0m Cleared {count} messages.```", delete_after=2)

@bot.command()
async def clear(ctx):
    """Clears RPC/Presence"""
    await bot.change_presence(activity=None, status=bot.status_dot)
    await ui_send(ctx, "RPC", "Cleared Presence.", "CLEAN", "32")

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = None
    bot.bio_messages = []
    bot.status_messages = []
    await bot.change_presence(activity=None)
    await ui_send(ctx, "STOP", "Wiped all data and halted.", "HALT", "31")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        Thread(target=run_flask, daemon=True).start()
        bot.run(TOKEN)
