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
def home(): return "ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ─── THE BOT CLASS ───
class Kill(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.react_target_id = None
        self.react_emojis = [] 
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []
        self.mock_target = None
        self.uwu_target = None

    async def on_ready(self):
        print(f"─── {self.user} IS LIVE ───")

    def update_bio(self, text):
        requests.patch("https://discord.com/api/v9/users/@me", 
                       headers={"Authorization": os.getenv("DISCORD_TOKEN")}, 
                       json={"bio": text})

    async def bio_rotator(self):
        while self.rotating_bio:
            for text in self.bio_messages:
                if not self.rotating_bio: break
                self.update_bio(text)
                await asyncio.sleep(45)

    async def status_rotator(self):
        while self.rotating_status:
            for text in self.status_messages:
                if not self.rotating_status: break
                await self.change_presence(activity=discord.CustomActivity(name=text))
                await asyncio.sleep(12)

    async def on_message(self, message):
        # PRIORITY 1: YOUR COMMANDS
        if message.author.id == self.user.id:
            await self.process_commands(message)
        
        # PRIORITY 2: AUTO-REACT
        if self.react_target_id and message.author.id == self.react_target_id:
            for e in self.react_emojis:
                try: await message.add_reaction(e.strip())
                except: pass

        # PRIORITY 3: TROLLING
        if self.mock_target and message.author.id == self.mock_target:
            await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
        if self.uwu_target and message.author.id == self.uwu_target:
            await message.channel.send(message.content.replace('L','W').replace('R','W').replace('l','w').replace('r','w') + " uwu")

bot = Kill()

# ─── SIMPLE UI (STOPS THE FAILED SENDING) ───
async def ui(ctx, title, body):
    try:
        msg = f"**[{title}]** {body}"
        await ctx.send(msg, delete_after=5)
    except:
        print(f"FAILED TO SEND UI: {title}")

# ─── COMMANDS ───
@bot.command()
async def multireact(ctx, *, args):
    try:
        bot.react_target_id = int(re.search(r'\d+', args).group())
        emoji_raw = re.sub(r'<@!?\d+>', '', args).strip()
        bot.react_emojis = (re.findall(r'<a?:\w+:\d+>', emoji_raw) + [c for c in emoji_raw.split() if not c.startswith('<')])[:3]
        await ui(ctx, "REACT", f"Locked onto {bot.react_target_id} with {len(bot.react_emojis)} emojis")
    except:
        await ui(ctx, "ERROR", "Mention someone and add emojis")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    await ui(ctx, "REACT", "Stopped")

@bot.command()
async def addbio(ctx, *, t):
    bot.bio_messages.append(t)
    await ui(ctx, "BIO", f"Added. Total: {len(bot.bio_messages)}")

@bot.command()
async def rotatebio(ctx, mode):
    bot.rotating_bio = (mode.lower() == "on")
    if bot.rotating_bio: bot.loop.create_task(bot.bio_rotator())
    await ui(ctx, "BIO", f"Rotation: {mode.upper()}")

@bot.command()
async def clearbio(ctx):
    bot.bio_messages = []; bot.rotating_bio = False
    await ui(ctx, "BIO", "List cleared")

@bot.command()
async def addstatus(ctx, *, t):
    bot.status_messages.append(t)
    await ui(ctx, "STATUS", f"Added. Total: {len(bot.status_messages)}")

@bot.command()
async def rotatestatus(ctx, mode):
    bot.rotating_status = (mode.lower() == "on")
    if bot.rotating_status: bot.loop.create_task(bot.status_rotator())
    await ui(ctx, "STATUS", f"Rotation: {mode.upper()}")

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []; bot.rotating_status = False
    await ui(ctx, "STATUS", "List cleared")

@bot.command()
async def mock(ctx, user: discord.User):
    bot.mock_target = user.id
    await ui(ctx, "MOCK", f"Targeting {user.name}")

@bot.command()
async def uwu(ctx, user: discord.User):
    bot.uwu_target = user.id
    await ui(ctx, "UWU", f"Targeting {user.name}")

@bot.command()
async def stop(ctx):
    bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = bot.mock_target = bot.uwu_target = None
    await ui(ctx, "SYSTEM", "All tasks killed")

@bot.command()
async def ping(ctx):
    await ui(ctx, "PONG", f"{round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
