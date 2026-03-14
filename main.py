import discord
import asyncio
import os
import re
import requests
import time
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
        self.react_target_id = None
        self.react_emojis = [] 
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []
        self.mock_target = None

    async def on_ready(self):
        print(f"─── {self.user} IS LIVE ───")

    # ─── THE "FORCE" STATUS UPDATE ───
    async def force_status(self, text):
        """Uses the raw gateway payload to bypass library limitations"""
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.custom, 
                name="Custom Status", 
                state=text
            )
        )

    async def on_message(self, message):
        if message.author.id == self.user.id:
            await self.process_commands(message)
        
        if self.react_target_id and message.author.id == self.react_target_id:
            for e in self.react_emojis:
                try: await message.add_reaction(e.strip())
                except: pass

        if self.mock_target and message.author.id == self.mock_target:
            try: await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
            except: pass

bot = Kill()

async def ui(ctx, title, body):
    await ctx.send(f"**[{title}]** {body}")

# ─── HELP PAGES (RESTORED) ───
@bot.command()
async def help(ctx, cat=None):
    if not cat:
        return await ui(ctx, "HELP", "Categories: `status`, `social`, `utility` (Usage: ,help status)")
    
    cat = cat.lower()
    if cat == "status":
        await ui(ctx, "STATUS", "`,addstatus [t]`, `,rotatestatus [on/off]`, `,clearstatus`, `,addbio [t]`, `,rotatebio [on/off]`")
    elif cat == "social":
        await ui(ctx, "SOCIAL", "`,multireact @u [emojis]`, `,stopreact`, `,mock @u`, `,stop`")
    elif cat == "utility":
        await ui(ctx, "UTIL", "`,purge [n]`, `,ping`, `,stop`")

# ─── STATUS & BIO ───
@bot.command()
async def addstatus(ctx, *, text):
    bot.status_messages.append(text)
    await ui(ctx, "STATUS", f"Added: {text}")

@bot.command()
async def rotatestatus(ctx, mode):
    bot.rotating_status = (mode.lower() == "on")
    if bot.rotating_status:
        async def status_loop():
            while bot.rotating_status:
                for s in bot.status_messages:
                    if not bot.rotating_status: break
                    await bot.force_status(s)
                    await asyncio.sleep(15)
        bot.loop.create_task(status_loop())
    await ui(ctx, "STATUS", f"Rotation: {mode.upper()}")

@bot.command()
async def addbio(ctx, *, text):
    bot.bio_messages.append(text)
    await ui(ctx, "BIO", "Added to list.")

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

# ─── SOCIAL ───
@bot.command()
async def multireact(ctx, *, args):
    try:
        id_search = re.search(r'\d{17,19}', args)
        if not id_search: return await ui(ctx, "ERR", "Mention a user.")
        bot.react_target_id = int(id_search.group())
        emoji_raw = re.sub(r'<@!?\d+>', '', args).strip()
        bot.react_emojis = emoji_raw.split()[:3]
        await ui(ctx, "REACT", f"Locked: {bot.react_target_id}")
    except: await ui(ctx, "ERR", "Fail.")

@bot.command()
async def mock(ctx, *, args):
    id_search = re.search(r'\d{17,19}', args)
    if id_search:
        bot.mock_target = int(id_search.group())
        await ui(ctx, "MOCK", f"Targeting: {bot.mock_target}")

# ─── UTILITY ───
@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: await msg.delete()
            except: pass
            await asyncio.sleep(0.1)

@bot.command()
async def ping(ctx):
    await ui(ctx, "PONG", f"{round(bot.latency * 1000)}ms")

@bot.command()
async def stop(ctx):
    bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = bot.mock_target = None
    await ui(ctx, "HALT", "All tasks killed.")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
