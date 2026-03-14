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
        # DICTIONARY ENGINE: {user_id: [emojis]}
        self.targets = {} 
        self.status_dot = discord.Status.online
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
        # Always process commands first
        await self.process_commands(message)

        # ─── MULTI-TARGET AUTO REACT ───
        if message.author.id in self.targets:
            if not message.content.startswith(self.command_prefix):
                for emoji in self.targets[message.author.id]:
                    try: await message.add_reaction(emoji.strip())
                    except: pass

        # ─── TROLLING LOGIC ───
        if message.author.id != self.user.id:
            if self.mock_target == message.author.id:
                await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
            if self.uwu_target == message.author.id:
                await message.channel.send(message.content.replace('r','w').replace('l','w') + " uwu")

bot = Kill()

async def ui_send(ctx, title, body, footer="v4.6", color="34"):
    ui_box = f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    try: await ctx.send(ui_box, delete_after=10)
    except: await ctx.send(f"**[{title}]** {body}")

# ─── THE TARGETING ENGINE ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
    """Adds a target. Works by mention, ID, 'me', or Reply."""
    target_id = None
    
    # 1. Check for Reply
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target_id = ref.author.id
        raw_emojis = args if args else "🔥"
    # 2. Check for "me"
    elif args and "me" in args.lower():
        target_id = bot.user.id
        raw_emojis = args.lower().replace("me", "").strip()
    # 3. Check for Mention/ID
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m:
            target_id = int(id_m.group())
            raw_emojis = re.sub(r'<@!?\d+>', '', args).strip()
    
    if target_id:
        # If no emojis provided, default to 🔥
        emojis = raw_emojis.split() if raw_emojis else ["🔥"]
        bot.targets[target_id] = emojis
        await ui_send(ctx, "AR ADDED", f"Target: {target_id}\nEmojis: {' '.join(emojis)}\nTotal Targets: {len(bot.targets)}", "SUCCESS", "32")
    else:
        await ui_send(ctx, "ERR", "Mention someone or reply.", "FAIL", "31")

@bot.command()
async def stopreact(ctx, *, args=None):
    """Usage: ,stopreact @user OR ,stopreact all"""
    if args and "all" in args.lower():
        bot.targets = {}
        await ui_send(ctx, "REACT", "Wiped all targets.", "CLEARED", "31")
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m:
            tid = int(id_m.group())
            if tid in bot.targets:
                del bot.targets[tid]
                await ui_send(ctx, "REACT", f"Removed: {tid}", "DELETED", "31")
    elif ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if ref.author.id in bot.targets:
            del bot.targets[ref.author.id]
            await ui_send(ctx, "REACT", f"Removed: {ref.author.id}", "DELETED", "31")

@bot.command()
async def targets(ctx):
    """List all active AR targets"""
    if not bot.targets:
        return await ui_send(ctx, "TARGETS", "No active targets.", "EMPTY", "34")
    
    body = "\n".join([f"[1;34m{k}[0m: {' '.join(v)}" for k, v in bot.targets.items()])
    await ui_send(ctx, "ACTIVE LIST", body, "DATABASE", "34")

# ─── TURBO UTILS ───

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(text); await asyncio.sleep(0.4) 

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: await msg.delete(); await asyncio.sleep(0.05) 
            except: pass

@bot.command()
async def help(ctx, category=None):
    if not category:
        body = "[1;34m,help status[0m\n[1;35m,help social[0m\n[1;31m,help util[0m"
        return await ui_send(ctx, "HELP MENU", body, "Select Category", "37")
    
    cat = category.lower()
    if cat == "social":
        body = "`,ar @u [e]` | `,ar me [e]`\n`,targets` | `,stopreact @u` | `,stopreact all`"
        await ui_send(ctx, "HELP: SOCIAL", body, "Trolling Tools", "36")
    elif cat == "util":
        body = "`,spam [n] [t]` | `,purge [n]` | `,ping` | `,stop`"
        await ui_send(ctx, "HELP: UTILITY", body, "Power Tools", "31")

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_status = False
    bot.targets = {}
    bot.mock_target = bot.uwu_target = None
    await ui_send(ctx, "STOP", "Everything wiped.", "CLEAN", "31")

@bot.command()
async def ping(ctx):
    await ui_send(ctx, "PONG", f"{round(bot.latency * 1000)}ms", "ACTIVE", "32")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
