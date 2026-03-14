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
        self.react_emojis = [] # Starts empty to avoid forced fire emoji
        self.status_dot = discord.Status.online
        self.rotating_status = False
        self.status_messages = []

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    async def on_message(self, message):
        await self.process_commands(message)

        # ─── STICKY AUTO-REACT ───
        if self.react_target_id and message.author.id == self.react_target_id:
            # Don't react to your own commands to keep things clean
            if not message.content.startswith(self.command_prefix):
                for emoji in self.react_emojis:
                    try: await message.add_reaction(emoji.strip())
                    except: pass

        # ─── TROLLING LOGIC ───
        if message.author.id != self.user.id:
            if self.mock_target and message.author.id == self.mock_target:
                await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))
            if self.uwu_target and message.author.id == self.uwu_target:
                await message.channel.send(message.content.replace('r','w').replace('l','w') + " uwu")

bot = Kill()

async def ui_send(ctx, title, body, footer="v4.4", color="34"):
    ui_box = f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    try: await ctx.send(ui_box, delete_after=10)
    except: await ctx.send(f"**[{title}]** {body}")

# ─── THE PRECISION AR COMMANDS ───

@bot.command(aliases=['ar', 'mr'])
async def autoreact(ctx, *, args=None):
    """
    Usage:
    1. ,ar @user 🔥 💀 (Sets target and specific emojis)
    2. ,ar me 👑 (Sets you and specific emojis)
    3. [Reply to message] ,ar 🤡 (Targets that person)
    """
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
        bot.react_target_id = target_id
        # Split emojis and filter out empty strings; if none provided, default to 🔥
        final_emojis = raw_emojis.split() if raw_emojis else ["🔥"]
        bot.react_emojis = final_emojis
        
        await ui_send(ctx, "AUTO-REACT", f"Target: {target_id}\nEmojis: {' '.join(bot.react_emojis)}", "LOCKED", "32")
    else:
        await ui_send(ctx, "ERR", "Mention someone or reply to them.", "FAIL", "31")

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    bot.react_emojis = []
    await ui_send(ctx, "REACT", "Cleared and Stopped.", "OFF", "31")

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
        body = "`,ar @u [emojis]` | `,ar me [emojis]`\n`,mock @u` | `,uwu @u` | `,stopreact`"
        await ui_send(ctx, "HELP: SOCIAL", body, "Trolling Tools", "36")
    else:
        await ui_send(ctx, "HELP", "Use `,help social` to see the new AR logic.", "INFO", "34")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
