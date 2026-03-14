import discord
import asyncio
import os
import re
import time
import random
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

# ─── CONFIG ───
TOKEN = os.getenv("DISCORD_TOKEN")

class Kill(commands.Bot):
    def __init__(self, display_name="Main"):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.spamming = False
        self.target_id = None
        self.react_emoji = None
        self.afk_reason = None
        self.afk_time = 0
        self.afk_pings = 0
        self.afk_log = []  # Stores names of people who pinged
        self.rotating_status = False
        self.status_messages = []
        self.status_dot = discord.Status.online
        self.dm_running = False
        self.mock_target = None
        self.uwu_target = None

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    async def status_rotator(self):
        while self.rotating_status:
            if not self.status_messages: break
            for text in self.status_messages:
                if not self.rotating_status: break
                await self.change_presence(
                    activity=discord.CustomActivity(name=text),
                    status=self.status_dot
                )
                await asyncio.sleep(5)

    def sPoNgEbOb(self, text):
        return "".join([char.upper() if i % 2 == 0 else char.lower() for i, char in enumerate(text)])

    def uwuify(self, text):
        text = text.replace('L', 'W').replace('R', 'W').replace('l', 'w').replace('r', 'w')
        suffix = random.choice([" uwu", " owo", " >w<", " :3"])
        return text + suffix

    async def on_message(self, message):
        if message.author.id != self.user.id:
            # Social Logic
            if self.mock_target and message.author.id == self.mock_target:
                try: await message.channel.send(self.sPoNgEbOb(message.content))
                except: pass
            
            if self.uwu_target and message.author.id == self.uwu_target:
                try: await message.channel.send(self.uwuify(message.content))
                except: pass

            # AFK Responder & Logger
            if self.afk_reason and self.user.mentioned_in(message):
                self.afk_pings += 1
                log_entry = f"**{message.author}** in #{message.channel}"
                if log_entry not in self.afk_log:
                    self.afk_log.append(log_entry)
                try: await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
                except: pass

            # Auto-React
            if self.target_id and self.react_emoji and message.author.id == self.target_id:
                try: await message.add_reaction(self.react_emoji)
                except: pass
        
        # Self Management
        if message.author.id == self.user.id:
            if message.content.startswith("**[AFK]**"): return
            if message.content.startswith(self.command_prefix):
                await self.process_commands(message)
                return
            if self.afk_reason:
                if (time.time() - self.afk_time) < 2: return
                
                # Report Log upon return
                log_text = "\n".join(self.afk_log) if self.afk_log else "No pings recorded."
                msg = (f"Welcome back!\n"
                       f"Total Pings: **{self.afk_pings}**\n"
                       f"[1;30mLogged Users:[0m\n{log_text}")
                
                self.afk_reason = None
                self.afk_pings = 0
                self.afk_log = []
                await ui_send(message.channel, "SYSTEM", msg, "AFK REMOVED", "32")

# ─── UI Helper (Set to 7 Seconds) ───
async def ui_send(ctx, title, body, footer="Selfbot", color="34"):
    ui = (f"```ansi\n"
          f"[1;{color}m┏━━━━━━ [ {title} ] ━━━━━━┓[0m\n"
          f"{body}\n"
          f"[1;30m┗━━ {footer} ━━┛[0m\n```")
    dest = ctx.channel if hasattr(ctx, 'channel') else ctx
    await dest.send(ui, delete_after=7)

# ─── Command Registration ───
def add_commands(bot: Kill):
    @bot.command()
    async def help(ctx, category: str = None):
        if category is None:
            title, color = "HELP MENU", "37"
            body = "[1;34m,help utility[0m\n[1;35m,help status[0m\n[1;31m,help social[0m"
        elif category.lower() == "utility":
            title, color = "UTILITY CMDS", "34"
            body = "[1;37m,afk [r][0m | [1;37m,purge [n][0m\n[1;37m,ping[0m | [1;37m,stop[0m"
        elif category.lower() == "status":
            title, color = "STATUS CMDS", "35"
            body = "[1;37m,dot [c][0m | [1;37m,rpc [t][0m\n[1;37m,addmsg [t][0m | [1;37m,rotate [on/off][0m"
        elif category.lower() == "social":
            title, color = "SOCIAL CMDS", "31"
            body = "[1;37m,mock [@u][0m | [1;37m,uwu [@u][0m\n[1;37m,unmock[0m | [1;37m,massdm [m][0m | [1;37m,spam [n] [t][0m"
        else: return
        await ui_send(ctx, title, body, f"Category: {category or 'Main'}", color)

    @bot.command()
    async def mock(ctx, target: str):
        bot.mock_target = int(re.search(r'\d+', target).group())
        bot.uwu_target = None
        await ui_send(ctx, "MOCK", f"Targeting: <@{bot.mock_target}>", "TROLLING", "31")

    @bot.command()
    async def uwu(ctx, target: str):
        bot.uwu_target = int(re.search(r'\d+', target).group())
        bot.mock_target = None
        await ui_send(ctx, "UWU", f"Targeting: <@{bot.uwu_target}>", "UWU", "35")

    @bot.command()
    async def unmock(ctx):
        bot.mock_target = bot.uwu_target = None
        await ui_send(ctx, "SOCIAL", "Targets cleared.", "CLEARED", "32")

    @bot.command()
    async def ping(ctx):
        await ui_send(ctx, "PONG", f"Latency: [1;32m{round(bot.latency * 1000)}ms[0m", "Active", "32")

    @bot.command()
    async def afk(ctx, *, reason="Away."):
        bot.afk_reason, bot.afk_time, bot.afk_pings, bot.afk_log = reason, time.time(), 0, []
        await ui_send(ctx, "AFK", f"Reason: {reason}", "SET", "33")

    @bot.command()
    async def purge(ctx, n: int):
        await ctx.channel.purge(limit=n, check=lambda m: m.author.id == bot.user.id)
        await ctx.send(f"```ansi\n[1;34m[ PURGE ][0m Cleared {n} messages.```", delete_after=2)

    @bot.command()
    async def rpc(ctx, *, text: str):
        await bot.change_presence(activity=discord.Streaming(name=text, url="https://twitch.tv/discord"), status=bot.status_dot)
        await ui_send(ctx, "RPC", f"Streaming: {text}", "RPC SET", "35")

    @bot.command()
    async def addmsg(ctx, *, text: str):
        bot.status_messages.append(text)
        await ui_send(ctx, "STATUS", f"Added: {text}", "ROTATOR", "32")

    @bot.command()
    async def rotate(ctx, toggle: str):
        if toggle.lower() == "on":
            bot.rotating_status = True
            bot.loop.create_task(bot.status_rotator())
            await ui_send(ctx, "ROTATOR", "ENABLED", "ON", "32")
        else:
            bot.rotating_status = False
            await ui_send(ctx, "ROTATOR", "DISABLED", "OFF", "31")

    @bot.command()
    async def dot(ctx, mode: str):
        modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "inv": discord.Status.invisible}
        bot.status_dot = modes.get(mode.lower(), discord.Status.online)
        await bot.change_presence(status=bot.status_dot)
        await ui_send(ctx, "DOT", f"Mode: {mode.upper()}", "UPDATED", "34")

    @bot.command()
    async def stop(ctx):
        bot.dm_running = bot.rotating_status = bot.spamming = False
        bot.target_id = bot.afk_reason = bot.mock_target = bot.uwu_target = None
        bot.afk_pings = 0
        bot.afk_log = []
        await bot.change_presence(activity=None)
        await ui_send(ctx, "SYSTEM", "Everything stopped.", "HALT", "31")

# ─── Execution ───
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    if TOKEN:
        master_bot = Kill()
        add_commands(master_bot)
        master_bot.run(TOKEN)
