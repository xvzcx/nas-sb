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
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []
        self.mock_target = None
        self.uwu_target = None
        self.react_target_id = None
        self.react_emojis = [] 
        self.status_dot = discord.Status.online
        
        # Profile Rotation States
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

    # ─── ROTATION LOOPS ───
    async def bio_rotator(self):
        while self.rotating_bio:
            if not self.bio_messages: break
            for text in self.bio_messages:
                if not self.rotating_bio: break
                self.update_profile_bio(text)
                await asyncio.sleep(45)

    async def status_rotator(self):
        while self.rotating_status:
            if not self.status_messages: break
            for text in self.status_messages:
                if not self.rotating_status: break
                try:
                    await self.change_presence(activity=discord.CustomActivity(name=text), status=self.status_dot)
                except: pass
                await asyncio.sleep(12)

    async def on_message(self, message):
        # ─── UNIVERSAL REACTION TRIGGER (Works for self & others) ───
        if self.react_target_id and message.author.id == self.react_target_id:
            for emoji in self.react_emojis:
                try: 
                    await message.add_reaction(emoji.strip())
                    await asyncio.sleep(0.05) 
                except: pass

        # ─── SELF-SPECIFIC LOGIC ───
        if message.author.id == self.user.id:
            await self.process_commands(message)
            if self.afk_reason and not message.content.startswith(self.command_prefix):
                if (time.time() - self.afk_time) > 3:
                    log_text = "\n".join(self.afk_log) if self.afk_log else "No pings."
                    await ui_send(message.channel, "SYSTEM", f"Back! Pings: {self.afk_pings}\n{log_text}", "AFK OFF", "32")
                    self.afk_reason, self.afk_pings, self.afk_log = None, 0, []
            return

        # ─── OTHERS-ONLY AUTOMATION ───
        if self.mock_target and message.author.id == self.mock_target:
            try: await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
            except: pass

        if self.uwu_target and message.author.id == self.uwu_target:
            try: await message.channel.send(message.content.replace('L','W').replace('R','W').replace('l','w').replace('r','w') + " uwu")
            except: pass

        if self.afk_reason and self.user.mentioned_in(message):
            self.afk_pings += 1
            self.afk_log.append(f"**{message.author}** in #{message.channel}")
            try: await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
            except: pass

# ─── UI HELPER ───
async def ui_send(ctx, title, body, footer="Selfbot v2.6", color="34"):
    ui = f"```ansi\n[1;{color}m┏━━━━ [ {title} ] ━━━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    target = ctx.channel if hasattr(ctx, 'channel') else ctx
    await target.send(ui, delete_after=7)

bot = Kill()

# ─── COMMANDS: STATUS & BIO ───
@bot.command()
async def addbio(ctx, *, text: str):
    bot.bio_messages.append(text)
    await ui_send(ctx, "BIO", f"Added: {text}\nTotal: {len(bot.bio_messages)}", "SAVED", "32")

@bot.command()
async def rotatebio(ctx, toggle: str):
    if toggle.lower() == "on":
        bot.rotating_bio = True
        bot.loop.create_task(bot.bio_rotator())
        await ui_send(ctx, "BIO", "Rotation: ON", "32")
    else:
        bot.rotating_bio = False
        await ui_send(ctx, "BIO", "Rotation: OFF", "31")

@bot.command()
async def clearbio(ctx):
    bot.bio_messages = []
    bot.rotating_bio = False
    await ui_send(ctx, "BIO", "List wiped.", "CLEARED", "31")

@bot.command()
async def addstatus(ctx, *, text: str):
    bot.status_messages.append(text)
    await ui_send(ctx, "STATUS", f"Added: {text}\nTotal: {len(bot.status_messages)}", "SAVED", "35")

@bot.command()
async def rotatestatus(ctx, toggle: str):
    if toggle.lower() == "on":
        bot.rotating_status = True
        bot.loop.create_task(bot.status_rotator())
        await ui_send(ctx, "STATUS", "Turbo Rotation: ON", "35")
    else:
        bot.rotating_status = False
        await ui_send(ctx, "STATUS", "Rotation: OFF", "31")

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []
    bot.rotating_status = False
    await ui_send(ctx, "STATUS", "List wiped.", "CLEARED", "31")

# ─── COMMANDS: SOCIAL & FUN ───
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

@bot.command()
async def mock(ctx, target: discord.User):
    bot.mock_target = target.id
    bot.uwu_target = None
    await ui_send(ctx, "MOCK", f"Target: {target.name}", "ACTIVE", "31")

@bot.command()
async def uwu(ctx, target: discord.User):
    bot.uwu_target = target.id
    bot.mock_target = None
    await ui_send(ctx, "UWU", f"Target: {target.name}", "ACTIVE", "35")

# ─── COMMANDS: UTILITY ───
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
async def afk(ctx, *, reason="Away"):
    bot.afk_reason, bot.afk_time = reason, time.time()
    await ui_send(ctx, "AFK", f"Reason: {reason}", "SET", "33")

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = None
    bot.mock_target = bot.uwu_target = None
    bot.bio_messages = []
    bot.status_messages = []
    await bot.change_presence(activity=None)
    await ui_send(ctx, "STOP", "Everything halted and cleared.", "HALT", "31")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
