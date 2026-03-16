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
bot.current_rpc = None # Store the current activity to re-apply if lost

# MDM CONFIG
MDM_DELAY = 3.5  
MDM_JITTER = 1.5 

@bot.event
async def on_ready():
    print(f"─── {bot.user} v11.4 | RPC STABILITY FIX ───")

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
        f"[1;31m Commands:[0m [1;30m{bot.command_prefix}help <cat>[0m\n"
        f"[1;30m├{'─'*(width-2)}┤[0m\n"
    )
    content = ""
    for line in body.split("\n"): content += f" {line}\n"
    foot = ""
    if footer: foot = (f"[1;30m├{'─'*(width-2)}┤[0m\n" f" [1;31m {footer}[0m\n")
    close = f"[1;30m╰{'─'*(width-2)}╯[0m"
    return f"```ansi\n{header}{content}{foot}{close}\n```"

# ─── HOSTING ENGINE ───

def run_isolated_bot(token):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    h_bot = commands.Bot(command_prefix=",", self_bot=True, help_command=None)
    
    @h_bot.event
    async def on_ready():
        print(f"--- [HOST SUCCESS] {h_bot.user} active. ---")

    try:
        loop.run_until_complete(h_bot.start(token))
    except Exception as e:
        print(f"--- [HOST CRASH] Error: {e} ---")
    finally:
        loop.close()

@bot.command()
async def host(ctx, token: str = None):
    await ctx.message.delete()
    if not token: return await ctx.send(ui_box("Error", "Missing Token"), delete_after=5)
    p = Process(target=run_isolated_bot, args=(token,), daemon=True)
    p.start()
    bot.hosted_processes[token] = p
    await ctx.send(ui_box("Hosting", "Process Spawned."), delete_after=5)

# ─── UTILITY COMMANDS ───

@bot.command()
async def rpc(ctx, mode, *, text):
    """Enhanced RPC with internal state storage"""
    await ctx.message.delete()
    m = mode.lower()
    try:
        if m == "play": act = discord.Game(name=text)
        elif m == "listen": act = discord.Activity(type=discord.ActivityType.listening, name=text)
        elif m == "watch": act = discord.Activity(type=discord.ActivityType.watching, name=text)
        else: return await ctx.send("Modes: play, listen, watch", delete_after=5)
        
        bot.current_rpc = act
        await bot.change_presence(activity=act, status=ctx.guild.me.status if ctx.guild else discord.Status.online)
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
    await bot.change_presence(activity=None)
    await ctx.send(ui_box("Status", "[1;31mPresence Cleared[0m"), delete_after=3)

@bot.command()
async def dot(ctx, mode=None):
    await ctx.message.delete()
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    target = modes.get(mode.lower(), discord.Status.online) if mode else discord.Status.online
    await bot.change_presence(status=target, activity=bot.current_rpc)
    await ctx.send(ui_box("Status Dot", f"Set to: {str(target).upper()}"), delete_after=3)

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
async def mdm(ctx, *, message: str = None):
    await ctx.message.delete()
    if not message: return await ctx.send("Usage: `,mdm <text>`", delete_after=5)
    targets = [m for g in bot.guilds for m in g.members if not m.bot and m.id != bot.user.id]
    random.shuffle(targets)
    sent, failed = 0, 0
    for member in targets:
        try:
            await member.send(message.replace("<ping>", member.mention).replace("<user>", member.display_name))
            sent += 1
        except: failed += 1
        await asyncio.sleep(MDM_DELAY + random.uniform(0, MDM_JITTER))
    await ctx.send(ui_box("MDM Done", f"Sent: {sent}\nFailed: {failed}"), delete_after=10)

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
async def stopreact(ctx, user: discord.User = None):
    await ctx.message.delete()
    if user is None: bot.targets = {}
    elif user.id in bot.targets: bot.targets.pop(user.id)
    await ctx.send("Stopped react tracking.", delete_after=3)

@bot.command()
async def help(ctx, cat=None):
    await ctx.message.delete()
    if not cat:
        body = "Status | Social | Utility"
        return await ctx.send(ui_box("Main Menu", body), delete_after=10)
    c = cat.lower()
    if c == "status": body = "`,rpc` `,streaming` `,afk` `,dot` `,clearstatus`"
    elif c == "social": body = "`,autoreact` `,stopreact` `,uwu` `,mock`"
    elif c == "utility": body = "`,spam` `,purge` `,mdm` `,host`"
    await ctx.send(ui_box(cat.title(), body), delete_after=10)

@bot.command()
async def stop(ctx):
    await ctx.message.delete()
    bot.spamming = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await ctx.send("All tasks halted.", delete_after=3)

if __name__ == "__main__":
    freeze_support()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        Thread(target=run_flask, daemon=True).start()
        bot.run(TOKEN)
