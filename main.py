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
# We enable message_content specifically to ensure commands are read.
intents = discord.Intents.default()
intents.message_content = True 

class Kill(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=",", self_bot=True, help_command=None, intents=intents)
        self.spamming = False
        self.mock_target = None
        self.uwu_target = None
        self.react_target_id = None
        self.react_emojis = [] 
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.status_dot = "online"
        self.status_messages = []
        self.bio_messages = []

    async def on_ready(self):
        print(f"─── {self.user} | COMMANDS READY ───")

    # We use a Listener instead of on_message so we DON'T block commands
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.user.id:
            # AFK Auto-Disable check
            if self.afk_reason and not message.content.startswith(","):
                if (time.time() - self.afk_time) > 5:
                    await message.channel.send(f"**[AFK OFF]**")
                    self.afk_reason = None
            return

        # Target Automations
        if self.react_target_id == message.author.id:
            for e in self.react_emojis:
                try: await message.add_reaction(e)
                except: pass

        if self.mock_target == message.author.id:
            await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
        
        if self.uwu_target == message.author.id:
            await message.channel.send(message.content.replace('l','w').replace('r','w') + " uwu")

bot = Kill()

# ─── ESSENTIAL COMMANDS ───

@bot.command()
async def dot(ctx, mode: str):
    """Checks if the bot can actually change its own state"""
    status_map = {"online": discord.Status.online, "dnd": discord.Status.dnd, "idle": discord.Status.idle}
    new_status = status_map.get(mode.lower(), discord.Status.online)
    await bot.change_presence(status=new_status)
    await ctx.send(f"**[DOT]** {mode}")

@bot.command()
async def mock(ctx, *, user_input):
    """Finds digits in your mention and targets them"""
    target_id = int(''.join(filter(str.isdigit, user_input)))
    bot.mock_target = target_id
    await ctx.send(f"**[MOCK]** Now bullying ID: {target_id}")

@bot.command()
async def unmock(ctx):
    bot.mock_target = bot.uwu_target = None
    await ctx.send("**[TROLL]** Cleared targets.")

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(text)
        await asyncio.sleep(1.2)

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: await msg.delete()
            except: pass
            await asyncio.sleep(0.2)

@bot.command()
async def ping(ctx):
    await ctx.send(f"**[PONG]** {round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
