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
        # Dict format: {user_id: [emoji_list]}
        self.targets = {} 
        self.status_dot = discord.Status.online

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.user} ───")

    async def on_message(self, message):
        await self.process_commands(message)

        # ─── MULTI-TARGET AUTO-REACT ───
        if message.author.id in self.targets:
            # Don't react to your own commands
            if not message.content.startswith(self.command_prefix):
                emojis = self.targets[message.author.id]
                for emoji in emojis:
                    try: 
                        await message.add_reaction(emoji.strip())
                    except: 
                        pass

        # ─── TROLLING LOGIC ───
        if message.author.id != self.user.id:
            if self.mock_target == message.author.id:
                await message.channel.send("".join([c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(message.content)]))

bot = Kill()

async def ui_send(ctx, title, body, footer="v4.5", color="34"):
    ui_box = f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{body}\n[1;30m┗━━ {footer} ━━┛[0m\n```"
    try: await ctx.send(ui_box, delete_after=10)
    except: await ctx.send(f"**[{title}]** {body}")

# ─── MULTI-AR COMMANDS ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
    """
    Usage: 
    ,ar @user 🔥 (Adds user to list)
    ,ar me 👑 (Adds you to list)
    """
    target_id = None
    
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target_id = ref.author.id
        raw_emojis = args if args else "🔥"
    elif args and "me" in args.lower():
        target_id = bot.user.id
        raw_emojis = args.lower().replace("me", "").strip()
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m:
            target_id = int(id_m.group())
            raw_emojis = re.sub(r'<@!?\d+>', '', args).strip()

    if target_id:
        emojis = raw_emojis.split() if raw_emojis else ["🔥"]
        # Add to the dictionary (this allows multiple targets)
        self.targets[target_id] = emojis
        
        await ui_send(ctx, "AR ADDED", f"Target: {target_id}\nTotal Targets: {len(self.targets)}", "MULTI-AR", "32")
    else:
        await ui_send(ctx, "ERR", "Mention someone or reply.", "FAIL", "31")

@bot.command()
async def stopreact(ctx, *, args=None):
    """
    Usage:
    ,stopreact @user (Removes one person)
    ,stopreact all (Clears everyone)
    """
    if args and "all" in args.lower():
        bot.targets = {}
        await ui_send(ctx, "REACT", "Cleared ALL targets.", "RESET", "31")
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m:
            tid = int(id_m.group())
            if tid in bot.targets:
                del bot.targets[tid]
                await ui_send(ctx, "REACT", f"Removed {tid}", "REMOVED", "31")
    elif ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        if ref.author.id in bot.targets:
            del bot.targets[ref.author.id]
            await ui_send(ctx, "REACT", f"Removed {ref.author.id}", "REMOVED", "31")

@bot.command()
async def listtargets(ctx):
    """Shows everyone currently being reacted to"""
    if not bot.targets:
        return await ui_send(ctx, "TARGETS", "No active targets.", "EMPTY", "34")
    
    list_str = "\n".join([f"ID: {k} | {' '.join(v)}" for k, v in bot.targets.items()])
    await ui_send(ctx, "ACTIVE TARGETS", list_str, "DATABASE", "34")

# ─── STANDARD UTILS ───

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for msg in ctx.channel.history(limit=n):
        if msg.author.id == bot.user.id:
            try: await msg.delete(); await asyncio.sleep(0.05) 
            except: pass

@bot.command()
async def stop(ctx):
    bot.targets = {}
    bot.spamming = False
    await ui_send(ctx, "HALT", "All targets and tasks cleared.", "CLEAN", "31")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
