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
bot.hosted_processes = {} # Track hosted tokens: {token: process_obj}

# MDM CONFIG
MDM_DELAY = 3.5  
MDM_JITTER = 1.5 

@bot.event
async def on_ready():
    print(f"─── {bot.user} v11.3 | STABLE HOSTING ENGINE ───")

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

# ─── HOSTING ENGINE (ISOLATION FIX) ───

def run_isolated_bot(token):
    """Deeply isolated worker to prevent main process interference"""
    try:
        # Create a completely separate event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Initialize a clean instance without any shared references
        h_bot = commands.Bot(command_prefix=",", self_bot=True, help_command=None)
        
        @h_bot.event
        async def on_ready():
            print(f"--- [HOST SUCCESS] {h_bot.user} is now running in an isolated process. ---")

        @h_bot.command()
        async def ping(ctx):
            await ctx.send(f"**Isolated Instance Active.** Latency: {int(h_bot.latency * 1000)}ms")

        h_bot.run(token)
    except Exception as e:
        print(f"--- [HOST CRASH] Error: {e} ---")

@bot.command()
async def host(ctx, token: str = None):
    await ctx.message.delete()
    if not token:
        return await ctx.send(ui_box("Host Error", "[1;31mMissing Token.[0m"), delete_after=5)
    
    if token in bot.hosted_processes:
        return await ctx.send(ui_box("Host Info", "[1;33mToken already active.[0m"), delete_after=5)
    
    try:
        # Use a daemon process so it dies if the main script stops
        p = Process(target=run_isolated_bot, args=(token,), daemon=True)
        p.start()
        
        # Small delay to see if it immediately fails
        await asyncio.sleep(1.5)
        if not p.is_alive():
            return await ctx.send(ui_box("Host Error", "[1;31mProcess died immediately.[0m\nCheck logs for details."), delete_after=10)
            
        bot.hosted_processes[token] = p
        await ctx.send(ui_box("Hosting", "[1;32mProcess Spawned.[0m\nInstance is initializing."), delete_after=10)
    except Exception as e:
        await ctx.send(ui_box("Host Error", f"[1;31mSpawn Failed: {e}[0m"), delete_after=5)

@bot.command()
async def stophost(ctx, token: str = None):
    await ctx.message.delete()
    if not token:
        count = len(bot.hosted_processes)
        for t, p in bot.hosted_processes.items():
            if p.is_alive(): p.terminate()
        bot.hosted_processes.clear()
        return await ctx.send(ui_box("Stop Host", f"[1;31mCLEARED {count} PROCESSES[0m"), delete_after=5)
    
    if token in bot.hosted_processes:
        p = bot.hosted_processes.pop(token)
        if p.is_alive(): p.terminate()
        await ctx.send(ui_box("Stop Host", "[1;31mPROCESS TERMINATED[0m"), delete_after=5)
    else:
        await ctx.send(ui_box("Stop Host", "[1;33mToken not found.[0m"), delete_after=5)

# ─── UTILITY COMMANDS ───

@bot.command()
async def dot(ctx, mode=None):
    await ctx.message.delete()
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    if not mode or mode.lower() not in modes:
        current = str(ctx.guild.me.status) if ctx.guild else "online"
        if current == "online": target = discord.Status.idle
        elif current == "idle": target = discord.Status.dnd
        else: target = discord.Status.online
    else:
        target = modes[mode.lower()]
    
    await bot.change_presence(status=target)
    await ctx.send(ui_box("Status Dot", f"[1;32mSet to:[0m {str(target).upper()}"), delete_after=3)

@bot.command()
async def mdm(ctx, *, message: str = None):
    await ctx.message.delete()
    if not message:
        usage = "[1;31mUsage:[0m `,mdm <text>`\n[1;34mVariables:[0m\n[1;30m▸[0m `<ping>` - Mentions user\n[1;30m▸[0m `<user>` - User's name"
        return await ctx.send(ui_box("MDM Help", usage), delete_after=15)
    
    targets = [m for g in bot.guilds for m in g.members if not m.bot and m.id != bot.user.id]
    random.shuffle(targets)
    status = await ctx.send(ui_box("MDM Engine", f"[1;33mScanned: {len(targets)} users[0m"))
    
    sent, failed = 0, 0
    for member in targets:
        try:
            content = message.replace("<ping>", member.mention).replace("<user>", member.display_name)
            await member.send(content)
            sent += 1
            if sent % 5 == 0: await status.edit(content=ui_box("MDM Active", f"[1;32mSent: {sent}[0m\n[1;31mFailed: {failed}[0m"))
        except: failed += 1
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
    await ctx.message.delete()
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        try:
            await ctx.send(text)
            await asyncio.sleep(0.25)
        except: await asyncio.sleep(1)

@bot.command()
async def ping(ctx):
    await ctx.send(ui_box("System", f"[1;32mLATENCY:[0m {int(bot.latency * 1000)}ms"), delete_after=5)

# ─── SOCIAL COMMANDS ───

@bot.command()
async def autoreact(ctx, user: discord.User, *, emojis):
    await ctx.message.delete()
    bot.targets[user.id] = emojis.split()
    await ctx.send(ui_box("Autoreact Add", f"[1;34mTarget:[0m {user.name}\n[1;34mReacts:[0m {emojis}"), delete_after=5)

@bot.command()
async def multireact(ctx, *, emojis):
    await ctx.message.delete()
    try:
        if ctx.message.reference:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            user = ref.author
            target_emojis = emojis.split()
        else:
            user = ctx.message.mentions[0]
            target_emojis = emojis.replace(f"<@{user.id}>", "").replace(f"<@!{user.id}>", "").strip().split()
        bot.targets[user.id] = target_emojis
        await ctx.send(ui_box("Multireact", f"[1;32mFollowing:[0m {user.name}\n[1;32mEmojis:[0m {' '.join(target_emojis)}"), delete_after=5)
    except: pass

@bot.command()
async def reactlog(ctx):
    await ctx.message.delete()
    if not bot.targets: return await ctx.send("`[!]` No active tracks.", delete_after=5)
    body = ""
    for tid, emojis in bot.targets.items():
        u = bot.get_user(tid)
        name = u.name if u else tid
        body += f"[1;34m{name}[0m [1;30m|[0m {' '.join(emojis)}\n"
    await ctx.send(ui_box("React Log", body), delete_after=15)

@bot.command()
async def stopreact(ctx, user: discord.User = None):
    await ctx.message.delete()
    if user is None:
        bot.targets = {}
        return await ctx.send(ui_box("Stopreact", "[1;31mALL TARGETS CLEARED[0m"), delete_after=3)
    if user.id in bot.targets:
        bot.targets.pop(user.id)
        await ctx.send(ui_box("Stopreact", f"[1;31mStopped:[0m {user.name}"), delete_after=3)

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

# ─── STATUS & HELP ───

@bot.command()
async def help(ctx, cat=None):
    await ctx.message.delete()
    if not cat:
        body = "[1;37mStatus  [1;31m|[0m [1;34mRPC & AFK commands[0m\n[1;37mSocial  [1;31m|[0m [1;34mReact & Troll commands[0m\n[1;37mUtility [1;31m|[0m [1;34mMisc & MDM engine[0m"
        return await ctx.send(ui_box("Main Menu", body), delete_after=15)
    c = cat.lower()
    if c == "status":
        body = "[1;30m▸[0m `,rpc` `,streaming` `,afk` `,afklog` `,dot`"
        await ctx.send(ui_box("Status", body), delete_after=10)
    elif c == "social":
        body = "[1;30m▸[0m `,autoreact` `,multireact` `,reactlog` `,stopreact` `,uwu` `,mock`"
        await ctx.send(ui_box("Social", body), delete_after=10)
    elif c == "utility":
        body = "[1;30m▸[0m `,spam` `,purge` `,ping` `,mdm` `,host` `,stophost`"
        await ctx.send(ui_box("Utility", body), delete_after=10)

@bot.command()
async def afk(ctx, *, reason="Away"):
    await ctx.message.delete()
    bot.afk_reason = reason
    bot.afk_log = []
    await ctx.send(ui_box("AFK", f"[1;33mREASON:[0m {reason}"), delete_after=5)

@bot.command()
async def afklog(ctx):
    await ctx.message.delete()
    if not bot.afk_log: return await ctx.send(ui_box("AFK Log", "[1;30mNo pings recorded.[0m"), delete_after=10)
    log_content = "\n".join(bot.afk_log[-15:])
    await ctx.send(ui_box("AFK Log", log_content), delete_after=20)

@bot.command()
async def rpc(ctx, mode, *, text):
    await ctx.message.delete()
    m = mode.lower()
    if m == "play": act = discord.Game(name=text)
    elif m == "listen": act = discord.Activity(type=discord.ActivityType.listening, name=text)
    elif m == "watch": act = discord.Activity(type=discord.ActivityType.watching, name=text)
    else: return
    await bot.change_presence(activity=act)
    await ctx.send(ui_box("Presence", f"[1;36m{m.upper()}ING[0m | [1;37m{text}[0m"), delete_after=3)

@bot.command()
async def streaming(ctx, *, text):
    await ctx.message.delete()
    await bot.change_presence(activity=discord.Streaming(name=text, url="https://twitch.tv/discord"))
    await ctx.send(ui_box("Stream", f"[1;35mStreaming:[0m {text}"), delete_after=3)

@bot.command()
async def stop(ctx):
    await ctx.message.delete()
    bot.spamming = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await ctx.send(ui_box("Halt", "[1;31mALL SYSTEMS STOPPED[0m"), delete_after=3)

if __name__ == "__main__":
    freeze_support()
    Thread(target=run_flask, daemon=True).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
