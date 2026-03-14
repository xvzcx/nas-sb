import discord
import asyncio
import os
import re
import time
import requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── KEEP-ALIVE ───
app = Flask(__name__)
@app.route('/')
def home(): return "STABLE"

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
        self.react_emojis = [] 
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []
        self.status_dot = "online"
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []

    async def on_ready(self):
        print(f"─── {self.user} | ALL SYSTEMS GREEN ───")

    async def force_status(self, text):
        """Raw Gateway Status Injection"""
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.custom, name="Custom Status", state=text),
            status=discord.Status.online if self.status_dot == "online" else discord.Status.dnd
        )

    async def on_message(self, message):
        if message.author.id == self.user.id:
            await self.process_commands(message)
            if self.afk_reason and not message.content.startswith(","):
                if (time.time() - self.afk_time) > 5:
                    await message.channel.send(f"**[AFK OFF]** Pings: {self.afk_pings}")
                    self.afk_reason, self.afk_pings = None, 0
            return

        # Automations
        if self.react_target_id == message.author.id:
            for e in self.react_emojis:
                try: await message.add_reaction(e)
                except: pass

        if self.mock_target == message.author.id:
            await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
        
        if self.uwu_target == message.author.id:
            await message.channel.send(message.content.replace('l','w').replace('r','w') + " uwu")

bot = Kill()

# ─── THE FULL COMMAND ARSENAL ───

@bot.command()
async def ping(ctx):
    await ctx.send(f"**[PONG]** {round(bot.latency * 1000)}ms")

@bot.command()
async def mock(ctx, *, args):
    # Extracts only digits (the ID) from the mention
    bot.mock_target = int(''.join(filter(str.isdigit, args)))
    await ctx.send(f"**[MOCK]** Targeted: {bot.mock_target}")

@bot.command()
async def uwu(ctx, *, args):
    bot.uwu_target = int(''.join(filter(str.isdigit, args)))
    await ctx.send(f"**[UWU]** Targeted: {bot.uwu_target}")

@bot.command()
async def unmock(ctx):
    bot.mock_target = bot.uwu_target = None
    await ctx.send("**[TROLL]** Disabled all.")

@bot.command()
async def addbio(ctx, *, t):
    bot.bio_messages.append(t)
    await ctx.send(f"**[BIO]** Added: {t}")

@bot.command()
async def rotatebio(ctx, mode):
    bot.rotating_bio = (mode.lower() == "on")
    if bot.rotating_bio:
        async def b_loop():
            while bot.rotating_bio:
                for b in bot.bio_messages:
                    requests.patch("https://discord.com/api/v9/users/@me", 
                        headers={"Authorization": os.getenv("DISCORD_TOKEN")}, json={"bio": b})
                    await asyncio.sleep(45)
        bot.loop.create_task(b_loop())
    await ctx.send(f"**[BIO]** Rotation: {mode.upper()}")

@bot.command()
async def addstatus(ctx, *, t):
    bot.status_messages.append(t)
    await ctx.send(f"**[STATUS]** Added: {t}")

@bot.command()
async def rotatestatus(ctx, mode):
    bot.rotating_status = (mode.lower() == "on")
    if bot.rotating_status:
        async def s_loop():
            while bot.rotating_status:
                for s in bot.status_messages:
                    await bot.force_status(s); await asyncio.sleep(12)
        bot.loop.create_task(s_loop())
    await ctx.send(f"**[STATUS]** Rotation: {mode.upper()}")

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []; bot.rotating_status = False
    await bot.change_presence(activity=None)
    await ctx.send("**[STATUS]** Wiped.")

@bot.command()
async def rpc(ctx, *, text):
    await bot.change_presence(activity=discord.Game(name=text))
    await ctx.send(f"**[RPC]** Playing: {text}")

@bot.command()
async def dot(ctx, mode):
    bot.status_dot = mode.lower()
    await bot.change_presence(status=discord.Status.dnd if mode == "dnd" else discord.Status.online)
    await ctx.send(f"**[DOT]** Set to: {mode}")

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: await msg.delete()
            except: pass
            await asyncio.sleep(0.1)

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(text); await asyncio.sleep(1.2)

@bot.command()
async def multireact(ctx, *, args):
    # Logic: grabs the first number as ID, then splits the rest as emojis
    parts = args.split()
    bot.react_target_id = int(''.join(filter(str.isdigit, parts[0])))
    bot.react_emojis = parts[1:4]
    await ctx.send(f"**[REACT]** Locked on {bot.react_target_id}")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    await ctx.send("**[REACT]** Stopped.")

@bot.command()
async def stop(ctx):
    bot.rotating_bio = bot.rotating_status = bot.spamming = False
    bot.mock_target = bot.uwu_target = bot.react_target_id = None
    await ctx.send("**[HALT]** Everything killed.")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
