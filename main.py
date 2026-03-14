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
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []
        self.mock_target = None
        self.uwu_target = None
        self.react_target_id = None
        self.react_emojis = [] 
        self.status_dot = discord.Status.online
        self.rotating_bio = False
        self.bio_messages = []

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    def update_bio(self, text):
        url = "https://discord.com/api/v9/users/@me/profile"
        headers = {"Authorization": os.getenv("DISCORD_TOKEN"), "Content-Type": "application/json"}
        data = {"bio": text}
        try: requests.patch(url, headers=headers, json=data)
        except: pass

    async def bio_rotator(self):
        while self.rotating_bio:
            if not self.bio_messages: break
            for text in self.bio_messages:
                if not self.rotating_bio: break
                self.update_bio(text)
                await asyncio.sleep(30)

    async def on_message(self, message):
        # ─── UNIVERSAL REACTION TRIGGER (Self & Others) ───
        if self.react_target_id and message.author.id == self.react_target_id:
            for emoji in self.react_emojis:
                try: 
                    await message.add_reaction(emoji.strip())
                    await asyncio.sleep(0.05) 
                except: pass

        # ─── SELF-COMMANDS ───
        if message.author.id == self.user.id:
            await self.process_commands(message)
            if self.afk_reason and not message.content.startswith(self.command_prefix):
                if (time.time() - self.afk_time) > 3:
                    log_text = "\n".join(self.afk_log) if self.afk_log else "No pings."
                    await ui_send(message.channel, "SYSTEM", f"Back! Pings: {self.afk_pings}\n{log_text}", "AFK OFF", "32")
                    self.afk_reason, self.afk_pings, self.afk_log = None, 0, []
            return

        # ─── OTHERS-ONLY ───
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
async def ui_send(ctx, title, body, footer="Selfbot", color="34"):
    ui = f"```ansi\n[1;{color}m┏━━━━ [ {title} ] ━━━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    target = ctx.channel if hasattr(ctx, 'channel') else ctx
    await target.send(ui, delete_after=7)

bot = Kill()

# ─── REBUILT MULTIREACT ───
@bot.command()
async def multireact(ctx, *, args: str):
    """Usage: ,multireact @user 🔥 💀 🤡"""
    try:
        # Extract the user ID from the mention manually
        user_id = int(re.search(r'\d+', args).group())
        
        # Remove the mention/ID part to leave just the emojis
        emoji_raw = re.sub(r'<@!?\d+>', '', args).strip()
        
        # Capture custom emojis and unicode emojis
        customs = re.findall(r'<a?:\w+:\d+>', emoji_raw)
        unicodes = [c for c in emoji_raw.split() if not c.startswith('<')]
        
        final_emojis = (customs + unicodes)[:3]
        
        if not final_emojis:
            return await ui_send(ctx, "ERROR", "No emojis detected.", "INPUT", "31")

        bot.react_target_id = user_id
        bot.react_emojis = final_emojis
        
        await ui_send(ctx, "MULTI-REACT", f"Target ID: {user_id}\nEmojis: {' '.join(final_emojis)}", "LOCKED", "32")
    except Exception as e:
        await ui_send(ctx, "ERROR", f"Invalid input. Mention a user.", "FAIL", "31")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    bot.react_emojis = []
    await ui_send(ctx, "MULTI-REACT", "Disabled.", "OFF", "31")

# ─── TURBO COMMANDS ───
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
async def spam(ctx, amount: int, *, text: str):
    bot.spamming = True
    await ctx.message.delete()
    for _ in range(amount):
        if not bot.spamming: break
        try:
            await ctx.send(text)
            await asyncio.sleep(0.12)
        except: break
    bot.spamming = False

# ─── REMAINING SYSTEM ───
@bot.command()
async def help(ctx, category=None):
    if not category:
        body = "[1;34m,help utility[0m\n[1;35m,help status[0m\n[1;31m,help social[0m"
        await ui_send(ctx, "HELP MENU", body, "v2.0", "37")
    elif category.lower() == "utility":
        body = "[1;37m,purge [n][0m | [1;37m,spam [n] [t][0m\n[1;37m,afk [r][0m | [1;37m,ping[0m | [1;37m,stop[0m"
        await ui_send(ctx, "UTILITY", body, "Turbo", "34")
    elif category.lower() == "status":
        body = "[1;37m,addbio [t][0m | [1;37m,rotatebio [on/off][0m\n[1;37m,rpc [t][0m | [1;37m,clear[0m | [1;37m,dot [mode][0m"
        await ui_send(ctx, "STATUS", body, "Profiles", "35")
    elif category.lower() == "social":
        body = "[1;37m,mock [@u][0m | [1;37m,uwu [@u][0m\n[1;37m,multireact [@u] [e..][0m | [1;37m,stopreact[0m"
        await ui_send(ctx, "SOCIAL", body, "Automation", "31")

@bot.command()
async def rpc(ctx, *, text: str):
    await bot.change_presence(activity=discord.Streaming(name=text, url="https://twitch.tv/discord"), status=bot.status_dot)
    await ui_send(ctx, "RPC", f"Streaming: {text}", "SET", "35")

@bot.command()
async def clear(ctx):
    await bot.change_presence(activity=None, status=bot.status_dot)
    await ui_send(ctx, "STATUS", "Cleared.", "CLEAN", "32")

@bot.command()
async def dot(ctx, mode: str):
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "inv": discord.Status.invisible}
    bot.status_dot = modes.get(mode.lower(), discord.Status.online)
    await bot.change_presence(status=bot.status_dot)
    await ui_send(ctx, "DOT", f"Status: {mode.upper()}", "UPDATED", "34")

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_bio = False
    bot.mock_target = bot.uwu_target = bot.afk_reason = bot.react_target_id = None
    bot.react_emojis = []
    await bot.change_presence(activity=None)
    await ui_send(ctx, "STOP", "Killed all tasks.", "HALT", "31")

@bot.command()
async def ping(ctx):
    await ui_send(ctx, "PONG", f"{round(bot.latency * 1000)}ms", "Active", "32")

@bot.command()
async def afk(ctx, *, reason="Away"):
    bot.afk_reason, bot.afk_time = reason, time.time()
    await ui_send(ctx, "AFK", f"Reason: {reason}", "SET", "33")

@bot.command()
async def addbio(ctx, *, text: str):
    bot.bio_messages.append(text)
    await ui_send(ctx, "BIO", f"Added: {text}", "SAVED", "32")

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
async def mock(ctx, target: discord.User):
    bot.mock_target = target.id
    bot.uwu_target = None
    await ui_send(ctx, "MOCK", f"Target: {target.name}", "ACTIVE", "31")

@bot.command()
async def uwu(ctx, target: discord.User):
    bot.uwu_target = target.id
    bot.mock_target = None
    await ui_send(ctx, "UWU", f"Target: {target.name}", "ACTIVE", "35")

@bot.command()
async def unmock(ctx):
    bot.mock_target = bot.uwu_target = None
    await ui_send(ctx, "SOCIAL", "Mock/UwU disabled.", "CLEARED", "32")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        Thread(target=run_flask, daemon=True).start()
        bot.run(TOKEN)
