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
        self.mock_target = None
        self.uwu_target = None
        self.react_target_id = None
        self.last_react_id = None # Store for autoreact toggle
        self.react_emojis = [] 
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []
        self.status_dot = discord.Status.online
        self.rotating_bio = False
        self.bio_messages = []
        self.rotating_status = False
        self.status_messages = []

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    async def force_status_update(self, text):
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.custom, name="Custom Status", state=text),
            status=self.status_dot
        )

    async def on_message(self, message):
        if message.author.id == self.user.id:
            await self.process_commands(message)
            if self.afk_reason and not message.content.startswith(self.command_prefix):
                if (time.time() - self.afk_time) > 3:
                    log_text = "\n".join(self.afk_log) if self.afk_log else "No pings."
                    await ui_send(message.channel, "WELCOME BACK", f"Pings: {self.afk_pings}\n{log_text}", "AFK OFF", "32")
                    self.afk_reason, self.afk_pings, self.afk_log = None, 0, []
            return

        if self.react_target_id and message.author.id == self.react_target_id:
            for emoji in self.react_emojis:
                try: await message.add_reaction(emoji.strip())
                except: pass

        if self.mock_target and message.author.id == self.mock_target:
            try: await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
            except: pass

        if self.uwu_target and message.author.id == self.uwu_target:
            try: await message.channel.send(message.content.replace('r','w').replace('l','w') + " uwu")
            except: pass

        if self.afk_reason and self.user.mentioned_in(message):
            self.afk_pings += 1
            self.afk_log.append(f"**{message.author}** in #{message.channel}")
            try: await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
            except: pass

bot = Kill()

async def ui_send(ctx, title, body, footer="Selfbot v4.0", color="34"):
    ui_box = f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    try: await ctx.send(ui_box, delete_after=10)
    except: await ctx.send(f"**[{title}]** {body}")

# ─── UPDATED HELP SYSTEM ───

@bot.command()
async def help(ctx, category=None):
    if not category:
        body = "[1;34m,help status[0m\n[1;35m,help social[0m\n[1;31m,help util[0m"
        return await ui_send(ctx, "HELP MENU", body, "Select Category", "37")
    
    cat = category.lower()
    if cat == "status":
        body = "`,addstatus [t]` | `,rotatestatus [on/off]`\n`,addbio [t]` | `,rotatebio [on/off]`\n`,rpc [text]` | `,dot [color]` | `,clearstatus`"
        await ui_send(ctx, "HELP: STATUS", body, "Profile Controls", "35")
    elif cat == "social":
        body = "`,mock @u` | `,uwu @u` | `,unmock`\n`,multireact @u [e]` | `,autoreact [on/off]` | `,stopreact`"
        await ui_send(ctx, "HELP: SOCIAL", body, "Trolling Tools", "36")
    elif cat == "util":
        body = "`,spam [n] [t]` | `,purge [n]`\n`,afk [reason]` | `,ping` | `,stop`"
        await ui_send(ctx, "HELP: UTILITY", body, "Power Tools", "31")

# ─── SOCIAL COMMANDS (INCLUDING AUTOREACT) ───

@bot.command()
async def multireact(ctx, *, args):
    try:
        user_id = int(re.search(r'\d+', args).group())
        emojis = re.sub(r'<@!?\d+>', '', args).strip().split()[:3]
        bot.react_target_id = user_id
        bot.last_react_id = user_id # Save for later toggle
        bot.react_emojis = emojis
        await ui_send(ctx, "REACT", f"Locked: {user_id}", "ACTIVE", "36")
    except: await ui_send(ctx, "ERR", "Mention + Emojis", "FAIL", "31")

@bot.command()
async def autoreact(ctx, toggle):
    if toggle.lower() == "on":
        if bot.last_react_id:
            bot.react_target_id = bot.last_react_id
            await ui_send(ctx, "REACT", f"Re-activated: {bot.react_target_id}", "ON", "32")
        else:
            await ui_send(ctx, "REACT", "No previous target found.", "FAIL", "31")
    else:
        bot.react_target_id = None
        await ui_send(ctx, "REACT", "Auto-react Disabled.", "OFF", "31")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    await ui_send(ctx, "REACT", "Stopped.", "OFF", "31")

# ─── TURBO UTILITY ───

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(text)
        await asyncio.sleep(0.4) 

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: 
                await msg.delete()
                await asyncio.sleep(0.05) 
            except: pass

# ─── THE REST ───

@bot.command()
async def addstatus(ctx, *, t):
    bot.status_messages.append(t); await ui_send(ctx, "STATUS", f"Added. Total: {len(bot.status_messages)}", "SAVED", "35")

@bot.command()
async def rotatestatus(ctx, toggle):
    bot.rotating_status = (toggle.lower() == "on")
    if bot.rotating_status:
        async def s_rot():
            while bot.rotating_status:
                for t in bot.status_messages:
                    if not bot.rotating_status: break
                    await bot.force_status_update(t); await asyncio.sleep(12)
        bot.loop.create_task(s_rot())
    await ui_send(ctx, "STATUS", f"Rotation: {toggle.upper()}", "ACTIVE", "32")

@bot.command()
async def rpc(ctx, *, text):
    await bot.change_presence(activity=discord.Game(name=text)); await ui_send(ctx, "RPC", f"Playing: {text}", "GAME", "34")

@bot.command()
async def dot(ctx, mode):
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    bot.status_dot = modes.get(mode.lower(), discord.Status.online)
    await bot.change_presence(status=bot.status_dot); await ui_send(ctx, "DOT", f"Set: {mode.upper()}", "UPDATED", "34")

@bot.command()
async def mock(ctx, *, args):
    id_m = re.search(r'\d+', args)
    if id_m: bot.mock_target = int(id_m.group()); bot.uwu_target = None; await ui_send(ctx, "MOCK", f"Target: {bot.mock_target}", "ACTIVE", "31")

@bot.command()
async def uwu(ctx, *, args):
    id_m = re.search(r'\d+', args)
    if id_m: bot.uwu_target = int(id_m.group()); bot.mock_target = None; await ui_send(ctx, "UWU", f"Target: {bot.uwu_target}", "ACTIVE", "35")

@bot.command()
async def unmock(ctx):
    bot.mock_target = bot.uwu_target = None; await ui_send(ctx, "TROLL", "Disabled.", "OFF", "31")

@bot.command()
async def ping(ctx):
    await ui_send(ctx, "PONG", f"{round(bot.latency * 1000)}ms", "ACTIVE", "32")

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_bio = bot.rotating_status = False
    bot.react_target_id = bot.mock_target = bot.uwu_target = None
    await ui_send(ctx, "STOP", "Everything halted.", "CLEAN", "31")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
