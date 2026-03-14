import discord, asyncio, os, re, time, requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── KEEPALIVE ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"
def run_flask(): app.run(host='0.0.0.0', port=8080)

bot = commands.Bot(command_prefix=",", self_bot=True, help_command=None)

# --- GLOBAL REGISTRIES ---
bot.targets = {}       
bot.spamming = False
bot.mock_target = None
bot.uwu_target = None
bot.afk_reason = None
bot.afk_log = [] 
bot.status_messages = []
bot.rotating_status = False

@bot.event
async def on_ready():
    print(f"─── {bot.user} v7.5 STABLE ───")

@bot.event
async def on_message(message):
    # 1. ALWAYS process commands first
    await bot.process_commands(message)

    # 2. HARD FILTER FOR SELF-MESSAGES (AFK OFF LOGIC)
    if message.author.id == bot.user.id:
        if bot.afk_reason:
            if not message.content.startswith(bot.command_prefix) and "┏━" not in message.content and "**[AFK]**" not in message.content:
                bot.afk_reason = None
                await message.channel.send("`[AFK]` Disabled. Welcome back.", delete_after=3)
        return 

    # 3. LOGIC FOR OTHERS
    uid = message.author.id

    # AFK PING RESPONDER & LOGGER
    if bot.afk_reason and bot.user.mentioned_in(message) and not message.mention_everyone:
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = f"[1;30m[{timestamp}][0m [1;34m{message.author.name}[0m [1;30min[0m #{message.channel}"
        bot.afk_log.append(log_entry)
        await message.channel.send(f"**[AFK]** {bot.afk_reason}", delete_after=5)

    # STICKY AR ENGINE
    if uid in bot.targets:
        emojis = bot.targets[uid]
        for e in emojis:
            try:
                await message.add_reaction(e.strip())
                await asyncio.sleep(0.1)
            except:
                continue

    # TROLLING LOGIC
    if bot.mock_target == uid:
        await message.channel.send("".join([c.upper() if i%2==0 else c.lower() for i,c in enumerate(message.content)]))
    
    if bot.uwu_target == uid:
        uwu_map = str.maketrans({'r': 'w', 'l': 'w', 'R': 'W', 'L': 'W'})
        await message.channel.send(f"{message.content.translate(uwu_map)} uwu")

# ─── UI ENGINE ───
def ui(color, title, text):
    line = "━━━━━━━━━━━━━━━━━━━━"
    return (
        f"```ansi\n"
        f"[1;{color}m┏━ {title.center(16)} ━┓[0m\n"
        f"{text}\n"
        f"[1;30m┗━{line[:len(title)+4]}━┛[0m\n"
        f"```"
    )

# ─── PRESENCE COMMANDS ───

@bot.command()
async def rpc(ctx, mode, *, text):
    m = mode.lower()
    if m == "play": act = discord.Game(name=text)
    elif m == "listen": act = discord.Activity(type=discord.ActivityType.listening, name=text)
    elif m == "watch": act = discord.Activity(type=discord.ActivityType.watching, name=text)
    else: return await ctx.send(ui("31", "ERROR", "Modes: play, listen, watch"), delete_after=3)
    await bot.change_presence(activity=act)
    await ctx.send(ui("36", "PRESENCE", f"{m.title()}ing: [1;36m{text}[0m"), delete_after=3)

@bot.command()
async def streaming(ctx, *, text):
    await bot.change_presence(activity=discord.Streaming(name=text, url="https://twitch.tv/discord"))
    await ctx.send(ui("35", "STREAM", f"Streaming: [1;35m{text}[0m"), delete_after=3)

@bot.command()
async def dot(ctx, mode):
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    status = modes.get(mode.lower(), discord.Status.online)
    await bot.change_presence(status=status)
    await ctx.send(ui("32", "DOT", f"Mode: [1;32m{mode.upper()}[0m"), delete_after=3)

# ─── UTILITY COMMANDS ───

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    count = 0
    async for m in ctx.channel.history(limit=min(n * 5, 500)):
        if m.author.id == bot.user.id:
            try:
                await m.delete()
                count += 1
                if count >= n: break
                await asyncio.sleep(0.01)
            except: continue

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        try:
            await ctx.send(text)
            await asyncio.sleep(0.2)
        except discord.errors.Forbidden: break
        except: await asyncio.sleep(1)

@bot.command()
async def ping(ctx):
    start = time.perf_counter()
    message = await ctx.send("`Pinging...`")
    end = time.perf_counter()
    duration = (end - start) * 1000
    await message.edit(content=f"**Latency:** `{int(bot.latency * 1000)}ms` | **API:** `{int(duration)}ms`")

# ─── SOCIAL & REACT COMMANDS ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args):
    """Usage: ,ar @user emojis"""
    try:
        user = ctx.message.mentions[0]
        emojis = args.replace(f"<@{user.id}>", "").replace(f"<@!{user.id}>", "").strip().split()
        bot.targets[user.id] = emojis
        await ctx.send(ui("32", "AR ADDED", f"User: [1;32m{user.name}[0m\nReacts: {' '.join(emojis)}"), delete_after=5)
    except:
        await ctx.send(ui("31", "ERROR", "Usage: `,ar @user [emojis]`"), delete_after=3)

@bot.command(aliases=['mr'])
async def multireact(ctx, *, args):
    """Reacts multiple emojis to the replied-to message or a user's last message"""
    try:
        # Determine target message
        target_msg = None
        if ctx.message.reference:
            target_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            emojis = args.split()
        else:
            # If no reply, check if there's a mention and use their last message
            user = ctx.message.mentions[0]
            emojis = args.replace(f"<@{user.id}>", "").replace(f"<@!{user.id}>", "").strip().split()
            async for m in ctx.channel.history(limit=50):
                if m.author.id == user.id:
                    target_msg = m
                    break
        
        if target_msg:
            await ctx.message.delete()
            for e in emojis:
                try: await target_msg.add_reaction(e.strip())
                except: continue
        else:
            await ctx.send(ui("31", "ERROR", "Reply to a message or mention a user."), delete_after=3)
    except:
        await ctx.send(ui("31", "ERROR", "Usage: `,mr [emojis]` (reply) or `,mr @u [emojis]`"), delete_after=3)

@bot.command()
async def stopreact(ctx, *, args=None):
    """Stops AR for a user. Usage: ,stopreact @user or ,stopreact [id] or ,stopreact all"""
    if not args:
        # If no args, try to check if it's a reply
        if ctx.message.reference:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            tid = ref.author.id
            if tid in bot.targets:
                bot.targets.pop(tid)
                return await ctx.send(ui("31", "AR REMOVED", f"Stopped: [1;31m{ref.author.name}[0m"), delete_after=3)
        return await ctx.send(ui("31", "ERROR", "Mention a user or type 'all'"), delete_after=3)

    if args.lower() == "all":
        bot.targets = {}
        return await ctx.send(ui("31", "AR CLEARED", "All targets removed."), delete_after=3)

    # Try mention
    if ctx.message.mentions:
        user = ctx.message.mentions[0]
        if user.id in bot.targets:
            bot.targets.pop(user.id)
            await ctx.send(ui("31", "AR REMOVED", f"Stopped: [1;31m{user.name}[0m"), delete_after=3)
    # Try raw ID
    else:
        try:
            uid = int(args.strip())
            if uid in bot.targets:
                bot.targets.pop(uid)
                await ctx.send(ui("31", "AR REMOVED", f"Stopped ID: {uid}"), delete_after=3)
        except:
            await ctx.send(ui("31", "ERROR", "Target not found."), delete_after=3)

@bot.command()
async def reactlog(ctx):
    """Alias for targets, showing active AR tracks"""
    if not bot.targets:
        return await ctx.send(ui("34", "REACT LOG", "No active tracks."), delete_after=5)
    
    lines = []
    for tid, emojis in bot.targets.items():
        u = bot.get_user(tid)
        name = f"[1;34m{u.name}[0m" if u else f"[1;30mID:{tid}[0m"
        lines.append(f"[1;30m•[0m {name} [1;30m»[0m {' '.join(emojis)}")
    
    await ctx.send(ui("34", "ACTIVE TRACKS", "\n".join(lines)), delete_after=15)

@bot.command()
async def targets(ctx):
    """Legacy alias for reactlog"""
    await reactlog(ctx)

@bot.command()
async def uwu(ctx, *, args=None):
    id_m = None
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        id_m = ref.author.id
    elif args:
        match = re.search(r'\d+', args)
        if match: id_m = int(match.group())
    if id_m:
        bot.uwu_target = id_m
        user = bot.get_user(id_m) or await bot.fetch_user(id_m)
        await ctx.send(ui("35", "UWU TARGET", f"Targeting: [1;35m{user.name}[0m"), delete_after=5)

@bot.command()
async def afk(ctx, *, reason="Away"):
    bot.afk_reason = reason
    bot.afk_log = []
    await ctx.send(ui("33", "AFK", f"Status: [1;33mENABLED[0m\nReason: {reason}"), delete_after=5)

@bot.command()
async def afklog(ctx):
    if not bot.afk_log:
        return await ctx.send(ui("34", "AFK LOG", "No pings recorded."), delete_after=5)
    history = "\n".join(bot.afk_log[-10:])
    await ctx.send(ui("34", "AFK LOG", history), delete_after=15)

# ─── HELP & CORE ───

@bot.command()
async def help(ctx, cat=None):
    if not cat:
        body = "[1;34m» ,help status[0m\n[1;35m» ,help social[0m\n[1;31m» ,help utility[0m"
        return await ctx.send(ui("37", "MAIN MENU", body), delete_after=6)
    c = cat.lower()
    if c == "status":
        body = "[1;30m▸[0m `,rpc [m] [t]`   [1;30m▸ `,streaming [t]`\n[1;30m▸ `,afk [r]`       [1;30m▸ `,dot [mode]`\n[1;30m▸ `,afklog`"
        await ctx.send(ui("34", "STATUS", body), delete_after=8)
    elif c == "social":
        body = "[1;30m▸[0m `,ar @u [e]`  [1;30m▸ `,mr [e]`\n[1;30m▸ `,stopreact`  [1;30m▸ `,reactlog`\n[1;30m▸ `,uwu @u`      [1;30m▸ `,mock @u`"
        await ctx.send(ui("35", "SOCIAL", body), delete_after=8)
    elif c == "utility":
        body = "[1;30m▸[0m `,spam [n] [t]` [1;30m▸ `,purge [n]`\n[1;30m▸ `,stop`         [1;30m▸ `,ping`"
        await ctx.send(ui("31", "UTILITY", body), delete_after=8)

@bot.command()
async def stop(ctx):
    bot.spamming = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await bot.change_presence(activity=None)
    await ctx.send(ui("31", "HALT", "All tasks killed."), delete_after=3)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
