import discord, asyncio, os, re, time, requests, random
from discord.ext import commands
from flask import Flask
from threading import Thread

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

# MDM CONFIG
MDM_DELAY = 3.5  # Safe delay between DMs
MDM_JITTER = 1.5 # Random variance to bypass detection

@bot.event
async def on_ready():
    print(f"─── {bot.user} v10.2 | MDM INTEGRATED ───")

@bot.event
async def on_message(message):
    # CRITICAL: This line allows commands to work!
    await bot.process_commands(message)
    
    # Only proceed with auto-logic if it's NOT a command message
    if message.content.startswith(bot.command_prefix):
        return

    # If WE sent the message
    if message.author.id == bot.user.id:
        if bot.afk_reason:
            # Disable AFK if we start typing again
            if "╭──" not in message.content and "**[AFK]**" not in message.content:
                bot.afk_reason = None
                await message.channel.send("`[AFK]` Disabled. Welcome back.", delete_after=3)
        return 

    uid = message.author.id
    
    # AFK Auto-Reply
    if bot.afk_reason and bot.user.mentioned_in(message) and not message.mention_everyone:
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = f"[1;30m[{timestamp}][0m [1;34m{message.author.name}[0m in #{message.channel}"
        bot.afk_log.append(log_entry)
        await message.channel.send(f"**[AFK]** {bot.afk_reason}", delete_after=5)

    # Sticky Auto-React
    if uid in bot.targets:
        for e in bot.targets[uid]:
            try:
                await message.add_reaction(e.strip())
                await asyncio.sleep(0.1)
            except: continue

    # Mock Logic
    if bot.mock_target == uid:
        await message.channel.send(message.content)
    
    # Uwu Logic
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
    for line in body.split("\n"):
        content += f" {line}\n"
    
    foot = ""
    if footer:
        foot = (f"[1;30m├{'─'*(width-2)}┤[0m\n" f" [1;31m {footer}[0m\n")
        
    close = f"[1;30m╰{'─'*(width-2)}╯[0m"
    return f"```ansi\n{header}{content}{foot}{close}\n```"

# ─── UTILITY COMMANDS ───

@bot.command()
async def mdm(ctx, *, message: str):
    """Mass DM all unique users with placeholders: <ping> or <user>"""
    await ctx.message.delete()
    
    # Fetch all unique members across all servers
    targets = set()
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot and member.id != bot.user.id:
                targets.add(member)
    
    targets = list(targets)
    random.shuffle(targets) # Stealth randomization
    
    status = await ctx.send(ui_box("MDM Engine", f"[1;33mScanned: {len(targets)} users[0m\n[1;30mStarting sequence...[0m"))
    
    sent, failed = 0, 0
    for member in targets:
        try:
            # Placeholder replacement
            content = message.replace("<ping>", member.mention).replace("<user>", member.display_name)
            await member.send(content)
            sent += 1
            
            # Live Update UI
            if sent % 5 == 0:
                await status.edit(content=ui_box("MDM Active", f"[1;32mSent: {sent}[0m\n[1;31mFailed: {failed}[0m\n[1;30mTarget: {member.name}[0m"))
        except:
            failed += 1
        
        # Security Delay Jitter
        await asyncio.sleep(MDM_DELAY + random.uniform(0, MDM_JITTER))

    await status.edit(content=ui_box("MDM Complete", f"[1;32mTotal Sent: {sent}[0m\n[1;31mTotal Failed: {failed}[0m"))

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
                await asyncio.sleep(0.005)
            except: continue

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        try:
            await ctx.send(text)
            await asyncio.sleep(0.2)
        except:
            await asyncio.sleep(1)

@bot.command()
async def ping(ctx):
    await ctx.send(ui_box("System", f"[1;32mLATENCY:[0m {int(bot.latency * 1000)}ms"), delete_after=5)

# ─── SOCIAL COMMANDS ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args):
    try:
        user = ctx.message.mentions[0]
        emojis = args.replace(f"<@{user.id}>", "").replace(f"<@!{user.id}>", "").strip().split()
        bot.targets[user.id] = emojis
        await ctx.send(ui_box("AR Add", f"[1;34mTarget:[0m {user.name}\n[1;34mReacts:[0m {' '.join(emojis)}"), delete_after=5)
    except: pass

@bot.command(aliases=['rl'])
async def reactlog(ctx):
    if not bot.targets: return await ctx.send("`[!]` No active tracks.", delete_after=5)
    body = ""
    for tid, emojis in bot.targets.items():
        u = bot.get_user(tid)
        name = u.name if u else tid
        body += f"[1;34m{name}[0m [1;30m|[0m {' '.join(emojis)}\n"
    await ctx.send(ui_box("React Log", body), delete_after=15)

@bot.command(aliases=['sr'])
async def stopreact(ctx, *, args=None):
    if args and args.lower() == "all":
        bot.targets = {}
        return await ctx.send(ui_box("AR Clear", "[1;31mALL TARGETS REMOVED[0m"), delete_after=3)
    
    tid = None
    if ctx.message.mentions:
        tid = ctx.message.mentions[0].id
    
    if tid and tid in bot.targets:
        bot.targets.pop(tid)
        await ctx.send(ui_box("AR Stop", f"[1;31mRemoved ID:[0m {tid}"), delete_after=3)

@bot.command()
async def mock(ctx, user: discord.Member = None):
    if not user:
        bot.mock_target = None
        return await ctx.send(ui_box("Mock", "[1;31mMOCK DISABLED[0m"), delete_after=3)
    bot.mock_target = user.id
    await ctx.send(ui_box("Mock", f"[1;31mTargeting:[0m {user.name}"), delete_after=5)

@bot.command()
async def uwu(ctx, user: discord.Member = None):
    if not user:
        bot.uwu_target = None
        return await ctx.send(ui_box("Uwu", "[1;31mUWU DISABLED[0m"), delete_after=3)
    bot.uwu_target = user.id
    await ctx.send(ui_box("Uwu", f"[1;35mTargeting:[0m {user.name}"), delete_after=5)

# ─── STATUS & HELP ───

@bot.command()
async def help(ctx, cat=None):
    if not cat:
        body = (
            "[1;37mStatus  [1;31m|[0m [1;34mRPC & AFK commands[0m\n"
            "[1;37mSocial  [1;31m|[0m [1;34mReact & Troll commands[0m\n"
            "[1;37mUtility [1;31m|[0m [1;34mMisc & MDM engine[0m"
        )
        return await ctx.send(ui_box("Main Menu", body), delete_after=15)
    
    c = cat.lower()
    if c == "status":
        body = "[1;30m▸[0m `,rpc` `,streaming` `,afk`"
        await ctx.send(ui_box("Status", body), delete_after=10)
    elif c == "social":
        body = "[1;30m▸[0m `,ar` `,rl` `,sr` `,uwu` `,mock`"
        await ctx.send(ui_box("Social", body), delete_after=10)
    elif c == "utility":
        body = "[1;30m▸[0m `,spam` `,purge` `,ping` `,mdm`"
        await ctx.send(ui_box("Utility", body), delete_after=10)

@bot.command()
async def afk(ctx, *, reason="Away"):
    bot.afk_reason = reason
    await ctx.send(ui_box("AFK", f"[1;33mREASON:[0m {reason}"), delete_after=5)

@bot.command()
async def rpc(ctx, mode, *, text):
    m = mode.lower()
    if m == "play": act = discord.Game(name=text)
    elif m == "listen": act = discord.Activity(type=discord.ActivityType.listening, name=text)
    elif m == "watch": act = discord.Activity(type=discord.ActivityType.watching, name=text)
    else: return
    await bot.change_presence(activity=act)
    await ctx.send(ui_box("Presence", f"[1;36m{m.upper()}ING[0m | [1;37m{text}[0m"), delete_after=3)

@bot.command()
async def stop(ctx):
    bot.spamming = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await ctx.send(ui_box("Halt", "[1;31mALL SYSTEMS STOPPED[0m"), delete_after=3)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
