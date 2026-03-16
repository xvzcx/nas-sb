import discord, asyncio, os, re, time, requests, random
from discord.ext import commands
from flask import Flask
from threading import Thread
from multiprocessing import Process, freeze_support

# ─── KEEPALIVE ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# Use self_bot=True and ensure we process commands from ourselves
bot = commands.Bot(command_prefix=",", self_bot=True, help_command=None)

# --- GLOBAL REGISTRIES ---
bot.targets = {}       
bot.spamming = False
bot.mock_target = None
bot.uwu_target = None
bot.afk_reason = None
bot.afk_log = [] 
bot.hosted_processes = {} 
bot.current_rpc = None 
bot.rotating = False

# MDM CONFIG
MDM_DELAY = 3.5  
MDM_JITTER = 1.5 

@bot.event
async def on_ready():
    print(f"─── {bot.user} v11.6 | FUN MODULE ADDED ───")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.content.startswith(bot.command_prefix): return
    uid = message.author.id

    if uid in bot.targets:
        for emoji in bot.targets[uid]:
            try:
                await message.add_reaction(emoji.strip())
                await asyncio.sleep(0.1)
            except: continue

    if uid == bot.user.id:
        if bot.afk_reason:
            if "╭──" not in message.content and "**[AFK]**" not in message.content:
                bot.afk_reason = None
                await message.channel.send("`[AFK]` Disabled. Welcome back.", delete_after=3)
        return 
    
    if bot.afk_reason and bot.user.mentioned_in(message) and not message.mention_everyone:
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = f"[1;30m[{timestamp}][0m [1;34m{message.author.name}[0m in #{message.channel}"
        bot.afk_log.append(log_entry)
        await message.channel.send(f"**[AFK]** {bot.afk_reason}", delete_after=5)

    if bot.mock_target == uid: await message.channel.send(message.content)
    if bot.uwu_target == uid:
        uwu_map = str.maketrans({'r': 'w', 'l': 'w', 'R': 'W', 'L': 'W'})
        await message.channel.send(f"{message.content.translate(uwu_map)} uwu")

# ─── UI ENGINE ───
def ui_box(title, body, footer=None):
    width = 34
    header = (
        f"[1;30m╭{'─'*(width-2)}╮[0m\n"
        f"[1;31m Category:[0m [1;37m{title}[0m\n"
        f"[1;30m├{'─'*(width-2)}┤[0m\n"
    )
    content = ""
    for line in body.split("\n"): content += f" {line}\n"
    foot = ""
    if footer: foot = (f"[1;30m├{'─'*(width-2)}┤[0m\n" f" [1;31m {footer}[0m\n")
    close = f"[1;30m╰{'─'*(width-2)}╯[0m"
    return f"```ansi\n{header}{content}{foot}{close}\n```"

# ─── STATUS ENGINE ───

@bot.command()
async def setstatus(ctx, *, text: str):
    """Sets a simple Custom Status"""
    await ctx.message.delete()
    await bot.change_presence(activity=discord.CustomActivity(name=text))
    bot.current_rpc = discord.CustomActivity(name=text)
    await ctx.send(ui_box("Status", f"[1;32mSet to:[0m {text}"), delete_after=3)

@bot.command()
async def rotatestatus(ctx, delay: int, *, statuses: str):
    """Rotates between multiple statuses separated by |"""
    await ctx.message.delete()
    if bot.rotating:
        bot.rotating = False
        return await ctx.send(ui_box("Rotate", "[1;31mRotation Stopped.[0m"), delete_after=3)
    
    status_list = [s.strip() for s in statuses.split("|")]
    bot.rotating = True
    await ctx.send(ui_box("Rotate", f"[1;32mActive:[0m {len(status_list)} modes"), delete_after=5)
    
    while bot.rotating:
        for s in status_list:
            if not bot.rotating: break
            await bot.change_presence(activity=discord.CustomActivity(name=s))
            await asyncio.sleep(delay)

@bot.command()
async def dot(ctx, mode=None):
    await ctx.message.delete()
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    target = modes.get(mode.lower(), discord.Status.online) if mode else discord.Status.online
    await bot.change_presence(status=target, activity=bot.current_rpc)
    await ctx.send(ui_box("Status Dot", f"Set to: {str(target).upper()}"), delete_after=3)

# ─── RPC ENGINE ───

@bot.command()
async def rpc(ctx, mode, *, text):
    await ctx.message.delete()
    m = mode.lower()
    try:
        if m == "play": act = discord.Game(name=text)
        elif m == "listen": act = discord.Activity(type=discord.ActivityType.listening, name=text)
        elif m == "watch": act = discord.Activity(type=discord.ActivityType.watching, name=text)
        else: return await ctx.send("Modes: play, listen, watch", delete_after=5)
        
        bot.current_rpc = act
        await bot.change_presence(activity=act)
        await ctx.send(ui_box("Presence", f"[1;36m{m.upper()}ING[0m\n{text}"), delete_after=3)
    except Exception as e:
        await ctx.send(f"RPC Error: {e}", delete_after=5)

@bot.command()
async def streaming(ctx, *, text):
    await ctx.message.delete()
    act = discord.Streaming(name=text, url="https://twitch.tv/discord")
    bot.current_rpc = act
    await bot.change_presence(activity=act)
    await ctx.send(ui_box("Stream", f"[1;35mStreaming:[0m {text}"), delete_after=3)

@bot.command()
async def clearstatus(ctx):
    await ctx.message.delete()
    bot.current_rpc = None
    bot.rotating = False
    await bot.change_presence(activity=None)
    await ctx.send(ui_box("Status", "[1;31mPresence Cleared[0m"), delete_after=3)

# ─── FUN ENGINE ───

@bot.command()
async def mock(ctx, user: discord.Member = None):
    await ctx.message.delete()
    if not user:
        bot.mock_target = None
        return await ctx.send(ui_box("Mock", "[1;31mMOCK DISABLED[0m"), delete_after=3)
    bot.mock_target = user.id
    await ctx.send(ui_box("Mock", f"[1;31mTargeting:[0m {user.name}"), delete_after=5)

@bot.command()
async def uwu(ctx, user: discord.Member = None):
    await ctx.message.delete()
    if not user:
        bot.uwu_target = None
        return await ctx.send(ui_box("Uwu", "[1;31mUWU DISABLED[0m"), delete_after=3)
    bot.uwu_target = user.id
    await ctx.send(ui_box("Uwu", f"[1;35mTargeting:[0m {user.name}"), delete_after=5)

@bot.command()
async def dicksize(ctx, user: discord.Member = None):
    await ctx.message.delete()
    target = user or ctx.author
    size = random.randint(1, 15)
    shaft = "=" * size
    await ctx.send(ui_box("Dick Size", f"[1;34m{target.name}'s size:[0m\n8{shaft}D"))

@bot.command()
async def gaymeter(ctx, user: discord.Member = None):
    await ctx.message.delete()
    target = user or ctx.author
    percent = random.randint(1, 100)
    await ctx.send(ui_box("Gay Meter", f"[1;35m{target.name}[0m is [1;37m{percent}%[0m gay 🏳️‍🌈"))

# ─── UTILITY COMMANDS ───

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    deleted = 0
    async for m in ctx.channel.history(limit=200):
        if m.author.id == bot.user.id:
            try:
                await m.delete()
                deleted += 1
                if deleted >= n: break
                await asyncio.sleep(0.01)
            except: continue

@bot.command()
async def spam(ctx, n: int, *, text):
    await ctx.message.delete()
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        try:
            await ctx.send(text)
            await asyncio.sleep(0.3)
        except: await asyncio.sleep(1)

# ─── SOCIAL COMMANDS ───

@bot.command()
async def autoreact(ctx, user: discord.User, *, emojis):
    await ctx.message.delete()
    bot.targets[user.id] = emojis.split()
    await ctx.send(ui_box("Autoreact", f"Target: {user.name}"), delete_after=5)

@bot.command()
async def help(ctx, cat=None):
    await ctx.message.delete()
    if not cat:
        body = "Status | Social | Utility | Fun"
        return await ctx.send(ui_box("Main Menu", body), delete_after=10)
    c = cat.lower()
    if c == "status": body = "`,setstatus` `,rotatestatus` `,rpc` `,streaming` `,dot` `,clearstatus`"
    elif c == "social": body = "`,autoreact` `,stopreact`"
    elif c == "fun": body = "`,mock` `,uwu` `,dicksize` `,gaymeter`"
    elif c == "utility": body = "`,spam` `,purge` `,mdm` `,host`"
    await ctx.send(ui_box(cat.title(), body), delete_after=10)

@bot.command()
async def stop(ctx):
    await ctx.message.delete()
    bot.spamming = False
    bot.rotating = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await ctx.send("All tasks halted.", delete_after=3)

if __name__ == "__main__":
    freeze_support()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        Thread(target=run_flask, daemon=True).start()
        bot.run(TOKEN)
