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
        print(f"─── {self.user} SESSION START ───")

    # ─── GATEWAY OVERRIDE FOR STATUS ───
    async def force_status(self, text):
        """Standard discord.py CustomActivity often fails; this uses the state field."""
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

# ─── THE ANSI UI ENGINE ───
async def ui_send(ctx, title, body, footer="Selfbot v3.0", color="34"):
    # ANSI Color Map: 31=Red, 32=Green, 33=Yellow, 34=Blue, 35=Magenta, 36=Cyan
    ui = (
        f"```ansi\n"
        f"[1;{color}m┏━━━━━ [ {title} ] ━━━━━┓[0m\n"
        f"{body}\n"
        f"[1;30m┗━━ {footer} ━━┛[0m\n"
        f"```"
    )
    try:
        await ctx.send(ui, delete_after=8)
    except:
        # Fallback if channel permissions block embeds/long messages
        await ctx.send(f"**[{title}]** {body}", delete_after=5)

# ─── HELP PAGES ───
@bot.command()
async def help(ctx, cat=None):
    if not cat:
        body = "[1;34m,help status[0m\n[1;35m,help social[0m\n[1;31m,help utility[0m"
        return await ui_send(ctx, "HELP MENU", body, "Select Category", "37")
    
    cat = cat.lower()
    if cat == "status":
        body = "[1;37m,addstatus [t][0m | [1;37m,rotatestatus [on/off][0m\n[1;37m,addbio [t][0m | [1;37m,rotatebio [on/off][0m"
        await ui_send(ctx, "STATUS CMD", body, "Profiles", "35")
    elif cat == "social":
        body = "[1;37m,multireact @u [e][0m | [1;37m,mock @u[0m\n[1;37m,stopreact[0m | [1;37m,stop[0m"
        await ui_send(ctx, "SOCIAL CMD", body, "Automation", "36")
    elif cat == "utility":
        body = "[1;37m,purge [n][0m | [1;37m,ping[0m | [1;37m,clearstatus/bio[0m"
        await ui_send(ctx, "UTILITY CMD", body, "Tools", "31")

# ─── STATUS & BIO ───
@bot.command()
async def addstatus(ctx, *, text):
    bot.status_messages.append(text)
    await ui_send(ctx, "STATUS", f"Added: {text}\nTotal: {len(bot.status_messages)}", "SAVED", "32")

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
        await ui_send(ctx, "STATUS", "Rotation: **ON**", "RUNNING", "32")
    else:
        await ui_send(ctx, "STATUS", "Rotation: **OFF**", "STOPPED", "31")

@bot.command()
async def addbio(ctx, *, text):
    bot.bio_messages.append(text)
    await ui_send(ctx, "BIO", f"Added: {text}", "SAVED", "32")

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
        await ui_send(ctx, "BIO", "Rotation: **ON**", "RUNNING", "32")
    else:
        await ui_send(ctx, "BIO", "Rotation: **OFF**", "STOPPED", "31")

# ─── SOCIAL ───
@bot.command()
async def multireact(ctx, *, args):
    try:
        id_match = re.search(r'\d{17,19}', args)
        if not id_match: return await ui_send(ctx, "ERR", "Mention a user.", "FAIL", "31")
        bot.react_target_id = int(id_match.group())
        emoji_raw = re.sub(r'<@!?\d+>', '', args).strip()
        bot.react_emojis = emoji_raw.split()[:3]
        await ui_send(ctx, "REACT", f"Target: {bot.react_target_id}\nEmojis: {' '.join(bot.react_emojis)}", "LOCKED", "32")
    except: await ui_send(ctx, "ERR", "Parse Error.", "FAIL", "31")

@bot.command()
async def mock(ctx, *, args):
    id_match = re.search(r'\d{17,19}', args)
    if id_match:
        bot.mock_target = int(id_match.group())
        await ui_send(ctx, "MOCK", f"Targeting: {bot.mock_target}", "ACTIVE", "33")

# ─── UTILITY ───
@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    count = 0
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: 
                await msg.delete()
                count += 1
            except: pass
            await asyncio.sleep(0.1)
    await ui_send(ctx, "PURGE", f"Cleaned {count} messages.", "DONE", "34")

@bot.command()
async def ping(ctx):
    await ui_send(ctx, "PONG", f"Latency: {round(bot.latency * 1000)}ms", "ACTIVE", "32")

@bot.command()
async def stop(ctx):
    bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = bot.mock_target = None
    bot.bio_messages = []
    bot.status_messages = []
    await bot.change_presence(activity=None)
    await ui_send(ctx, "HALT", "All systems wiped and stopped.", "CLEAN", "31")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
