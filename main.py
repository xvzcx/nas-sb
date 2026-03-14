import discord
import asyncio
import os
import re
import time
import random
import requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── SYSTEM PULSE (For Uptime/Gunicorn) ───
app = Flask(__name__)

@app.route('/')
def home():
    return "SYSTEM ONLINE"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ─── CONFIG ───
TOKEN = os.getenv("DISCORD_TOKEN")

class Kill(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.spamming = False
        self.target_id = None
        self.react_emoji = None
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []
        self.rotating_status = False
        self.status_messages = []
        self.status_dot = discord.Status.online
        self.dm_running = False
        self.mock_target = None
        self.uwu_target = None
        self.rotating_bio = False
        self.bio_messages = []

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    def update_bio(self, text):
        """Direct API call to update Profile Bio"""
        url = "https://discord.com/api/v9/users/@me/profile"
        headers = {"Authorization": TOKEN, "Content-Type": "application/json"}
        data = {"bio": text}
        try:
            requests.patch(url, headers=headers, json=data)
        except:
            pass

    async def status_rotator(self):
        while self.rotating_status:
            if not self.status_messages: break
            for text in self.status_messages:
                if not self.rotating_status: break
                await self.change_presence(activity=discord.CustomActivity(name=text), status=self.status_dot)
                await asyncio.sleep(5)

    async def bio_rotator(self):
        while self.rotating_bio:
            if not self.bio_messages: break
            for text in self.bio_messages:
                if not self.rotating_bio: break
                self.update_bio(text)
                await asyncio.sleep(30) # Safer interval for Bio updates

    def sPoNgEbOb(self, text):
        return "".join([char.upper() if i % 2 == 0 else char.lower() for i, char in enumerate(text)])

    def uwuify(self, text):
        text = text.replace('L', 'W').replace('R', 'W').replace('l', 'w').replace('r', 'w')
        suffix = random.choice([" uwu", " owo", " >w<", " :3"])
        return text + suffix

    async def on_message(self, message):
        if message.author.id != self.user.id:
            # 1. Mocking/UwU Logic
            if self.mock_target and message.author.id == self.mock_target:
                try: await message.channel.send(self.sPoNgEbOb(message.content))
                except: pass
            if self.uwu_target and message.author.id == self.uwu_target:
                try: await message.channel.send(self.uwuify(message.content))
                except: pass

            # 2. AFK Logger
            if self.afk_reason and self.user.mentioned_in(message):
                self.afk_pings += 1
                log_entry = f"**{message.author}** in #{message.channel}"
                if log_entry not in self.afk_log: self.afk_log.append(log_entry)
                try: await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
                except: pass

            # 3. Auto-React
            if self.target_id and self.react_emoji and message.author.id == self.target_id:
                try: await message.add_reaction(self.react_emoji)
                except: pass
        
        # Self-Commands & AFK Removal
        if message.author.id == self.user.id:
            if message.content.startswith("**[AFK]**"): return
            if message.content.startswith(self.command_prefix):
                await self.process_commands(message)
                return
            if self.afk_reason:
                if (time.time() - self.afk_time) < 2: return
                log_text = "\n".join(self.afk_log) if self.afk_log else "No pings recorded."
                msg = f"Welcome back!\nPings: **{self.afk_pings}**\n[1;30mLogged:[0m\n
