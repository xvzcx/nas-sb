import discord
import asyncio
import os
import re
import requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── KEEP-ALIVE SYSTEM ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ─── THE BOT CLASS ───
class Kill(commands.Bot):
    def __init__(self):
        # Intents are required in 2026 even for selfbots
        intents = discord.Intents.default()
        intents.message_content = True 
        
        super().__init__(
            command_prefix=",", 
            self_bot=True, 
            help_command=None, 
            intents=intents
        )
        
        # States
        self.react_target_id = None
        self.react_emojis = [] 
        self.status_dot = discord.Status.online
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []

    async def on_ready(self):
        print(f"Logged in as: {self.user} (ID: {self.user.id})")

    def update_profile_bio(self, text):
        url = "https://discord.com/api/v9/users/@me"
        headers = {"Authorization": os.getenv("DISCORD_TOKEN"), "Content-Type": "application/json"}
        requests.patch(url, headers=headers, json={"bio": text})

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
                await self.change_presence(activity=discord.CustomActivity(name=text), status=self.status_dot)
                await asyncio.sleep(12)

    # ─── THE FIX IS HERE ───
    async def on_message(self, message):
        # 1. Ignore messages not from you
        if message.author.id != self.user.id:
            # But still check if we need to auto-react to others
            if self.react_target_id and message.author.id == self.react_target_id:
                for emoji in self.react_emojis:
                    try: await message.add_reaction(emoji.strip())
                    except: pass
            return

        # 2. Process your commands
        await self.process_commands(message)

# ─── UI HELPER ───
async def ui_send(ctx, title, body, footer="v2.5", color="34"):
    ui = f"```ansi\n[1;{color}m┏━━━━ [ {title} ] ━━━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    await ctx.send(ui, delete_after=5)

bot = Kill()

# ─── ALL COMMANDS ───
@bot.command()
async def addstatus(ctx, *, text: str):
    bot.status_messages.append(text)
    await ui_send(ctx, "STATUS", f"Added: {text}\nTotal: {len(bot.status_messages)}", "SAVED", "35")

@bot.command()
async def rotatestatus(ctx, toggle: str):
    if toggle.lower() == "on":
        bot.rotating_status = True
        bot.loop.create_task(bot.status_rotator())
        await ui_send(ctx, "STATUS", "Turbo Rotation: **ON**", "12s", "35")
    else:
        bot.rotating_status = False
        await ui_send(ctx, "STATUS", "Rotation: **OFF**", "STOPPED", "31")

@bot.command()
async def addbio(ctx, *, text: str):
    bot.bio_messages.append(text)
    await ui_send(ctx, "BIO", f"Added: {text}", "SAVED", "32")

@bot.command()
async def rotatebio(ctx, toggle: str):
    if toggle.lower() == "on":
        bot.rotating_bio = True
        bot.loop.create_task(bot.bio_rotator())
        await ui_send(ctx, "BIO", "Rotation: **ON**", "45s", "32")
    else:
        bot.rotating_bio = False
        await ui_send(ctx, "BIO", "Rotation: **OFF**", "STOPPED", "31")

@bot.command()
async def clearbio(ctx):
    bot.bio_messages = []
    bot.rotating_bio = False
    await ui_send(ctx, "BIO", "Wiped bio list.", "CLEARED", "31")

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []
    bot.rotating_status = False
    await ui_send(ctx, "STATUS", "Wiped status list.", "CLEARED", "31")

@bot.command()
async def ping(ctx):
    await ui_send(ctx, "PONG", f"{round(bot.latency * 1000)}ms", "ACTIVE", "32")

@bot.command()
async def stop(ctx):
    bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = None
    bot.bio_messages = []
    bot.status_messages = []
    await bot.change_presence(activity=None)
    await ui_send(ctx, "STOP", "Everything halted.", "CLEAN", "31")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        Thread(target=run_flask, daemon=True).start()
        bot.run(TOKEN)
