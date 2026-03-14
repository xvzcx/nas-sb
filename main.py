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
# CRITICAL: Intents must be enabled for the bot to "see" messages to react to
intents = discord.Intents.default()
intents.message_content = True 

class Kill(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=",", self_bot=True, help_command=None, intents=intents)
        self.spamming = False
        self.targets = {} # {int(user_id): [emojis]}
        self.status_dot = discord.Status.online

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    async def on_message(self, message):
        # Always process commands first
        await self.process_commands(message)

        # ─── MULTI-TARGET AUTO REACT ───
        # We force the comparison to be integer-based
        author_id = int(message.author.id)
        
        if author_id in self.targets:
            # Don't react to your own commands
            if not message.content.startswith(self.command_prefix):
                emojis = self.targets[author_id]
                for emoji in emojis:
                    try: 
                        await message.add_reaction(emoji.strip())
                    except: 
                        pass

bot = Kill()

async def ui_send(ctx, title, body, footer="v4.7", color="34"):
    ui_box = f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    try: await ctx.send(ui_box, delete_after=10)
    except: await ctx.send(f"**[{title}]** {body}")

# ─── THE TARGETING ENGINE (FORCED INTEGERS) ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
    target_id = None
    
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target_id = int(ref.author.id)
        raw_emojis = args if args else "🔥"
    elif args and "me" in args.lower():
        target_id = int(bot.user.id)
        raw_emojis = args.lower().replace("me", "").strip()
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m:
            target_id = int(id_m.group())
            raw_emojis = re.sub(r'<@!?\d+>', '', args).strip()
    
    if target_id:
        emojis = raw_emojis.split() if raw_emojis else ["🔥"]
        # CRITICAL: Store key as integer
        bot.targets[target_id] = emojis
        await ui_send(ctx, "AR ADDED", f"Target: {target_id}\nEmojis: {' '.join(emojis)}\nActive: {len(bot.targets)}", "SUCCESS", "32")
    else:
        await ui_send(ctx, "ERR", "Mention or Reply.", "FAIL", "31")

@bot.command()
async def targets(ctx):
    if not bot.targets:
        return await ui_send(ctx, "TARGETS", "No active targets.", "EMPTY", "34")
    
    # Debug view: shows IDs and their assigned emojis
    body = "\n".join([f"[1;34m{k}[0m: {' '.join(v)}" for k, v in bot.targets.items()])
    await ui_send(ctx, "ACTIVE LIST", body, "DATABASE", "34")

@bot.command()
async def stopreact(ctx, *, args=None):
    if args and "all" in args.lower():
        bot.targets = {}
        await ui_send(ctx, "REACT", "Wiped all.", "CLEARED", "31")
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m:
            tid = int(id_m.group())
            if tid in bot.targets: del bot.targets[tid]
            await ui_send(ctx, "REACT", f"Removed: {tid}", "DELETED", "31")
    elif ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        tid = int(ref.author.id)
        if tid in bot.targets: del bot.targets[tid]
        await ui_send(ctx, "REACT", f"Removed: {tid}", "DELETED", "31")

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
async def stop(ctx):
    bot.spamming = False
    bot.targets = {}
    await ui_send(ctx, "HALT", "All cleared.", "CLEAN", "31")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
