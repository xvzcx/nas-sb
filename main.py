import discord
import asyncio
import os
import re
import requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── SYSTEM PULSE ───
app = Flask(__name__)
@app.route('/')
def home(): return "STABLE"

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

    async def on_ready(self):
        print(f"─── READY: {self.user} ───")

    async def on_message(self, message):
        # 1. ALWAYS PROCESS COMMANDS FIRST
        if message.author.id == self.user.id:
            await self.process_commands(message)
        
        # 2. AUTO-REACT LOGIC (Check if target is set)
        if self.react_target_id and message.author.id == self.react_target_id:
            for e in self.react_emojis:
                try: await message.add_reaction(e.strip())
                except: pass

        # 3. MOCK LOGIC
        if self.mock_target and message.author.id == self.mock_target:
            try:
                content = "".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)])
                await message.channel.send(content)
            except: pass

bot = Kill()

# ─── THE FAIL-PROOF UI ───
async def ui(ctx, title, body):
    await ctx.send(f"**[{title}]** {body}")

# ─── FIXED COMMANDS (RAW PARSING) ───

@bot.command()
async def multireact(ctx, *, args=None):
    if not args: return await ui(ctx, "ERR", "Usage: ,multireact @user 🔥")
    try:
        # Manually find the ID numbers in the message
        user_id = int(re.search(r'\d+', args).group())
        # Strip the ID out to get the emojis
        emojis = re.sub(r'<@!?\d+>', '', args).strip().split()
        
        bot.react_target_id = user_id
        bot.react_emojis = emojis[:3]
        await ui(ctx, "REACT", f"Locked: {user_id} | Emojis: {' '.join(bot.react_emojis)}")
    except:
        await ui(ctx, "ERR", "Could not parse ID/Emojis.")

@bot.command()
async def addbio(ctx, *, text):
    bot.bio_messages.append(text)
    await ui(ctx, "BIO", f"Added. Total: {len(bot.bio_messages)}")

@bot.command()
async def rotatebio(ctx, mode):
    bot.rotating_bio = (mode.lower() == "on")
    if bot.rotating_bio:
        async def bio_loop():
            while bot.rotating_bio:
                for b in bot.bio_messages:
                    if not bot.rotating_bio: break
                    requests.patch("https://discord.com/api/v9/users/@me", 
                                   headers={"Authorization": os.getenv("DISCORD_TOKEN")}, 
                                   json={"bio": b})
                    await asyncio.sleep(45)
        bot.loop.create_task(bio_loop())
    await ui(ctx, "BIO", f"Rotation: {mode.upper()}")

@bot.command()
async def addstatus(ctx, *, text):
    bot.status_messages.append(text)
    await ui(ctx, "STATUS", f"Added. Total: {len(bot.status_messages)}")

@bot.command()
async def rotatestatus(ctx, mode):
    bot.rotating_status = (mode.lower() == "on")
    if bot.rotating_status:
        async def status_loop():
            while bot.rotating_status:
                for s in bot.status_messages:
                    if not bot.rotating_status: break
                    await bot.change_presence(activity=discord.CustomActivity(name=s))
                    await asyncio.sleep(12)
        bot.loop.create_task(status_loop())
    await ui(ctx, "STATUS", f"Rotation: {mode.upper()}")

@bot.command()
async def mock(ctx, *, args):
    try:
        user_id = int(re.search(r'\d+', args).group())
        bot.mock_target = user_id
        await ui(ctx, "MOCK", f"Targeting ID: {user_id}")
    except:
        await ui(ctx, "ERR", "Mention a user.")

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []
    bot.rotating_status = False
    await ui(ctx, "STATUS", "Cleared.")

@bot.command()
async def clearbio(ctx):
    bot.bio_messages = []
    bot.rotating_bio = False
    await ui(ctx, "BIO", "Cleared.")

@bot.command()
async def stop(ctx):
    bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = bot.mock_target = None
    await ui(ctx, "HALT", "Everything stopped.")

@bot.command()
async def ping(ctx):
    await ui(ctx, "PONG", f"{round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
