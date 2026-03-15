import discord, asyncio, os, re, time, requests, random
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

# MDM SETTINGS (From Integrated Script)
MDM_BLACKLIST = set()
BASE_DELAY = 3.0
JITTER_MIN = 0.5
JITTER_MAX = 2.0
DEFAULT_TEMPLATE = "<ping> yo check your DMs!"

@bot.event
async def on_ready():
    print(f"─── {bot.user} v9.0 | UI & MDM READY ───")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    
    if message.author.id == bot.user.id:
        if bot.afk_reason:
            if not message.content.startswith(bot.command_prefix) and "╭──" not in message.content and "**[AFK]**" not in message.content:
                bot.afk_reason = None
                await message.channel.send("`[AFK]` Disabled. Welcome back.", delete_after=3)
        return 

    uid = message.author.id
    
    # AFK Logic
    if bot.afk_reason and bot.user.mentioned_in(message) and not message.mention_everyone:
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = f"[1;30m[{timestamp}][0m [1;34m{message.author.name}[0m in #{message.channel}"
        bot.afk_log.append(log_entry)
        await message.channel.send(f"**[AFK]** {bot.afk_reason}", delete_after=5)

    # Sticky Auto-React
    if uid in bot.targets:
        for e in bot.targets[uid]:
            try:
                await message.add_reaction(e.strip())
                await asyncio.sleep(0.1)
            except: continue

    # Mock Logic (Exact mimic)
    if bot.mock_target == uid:
        await message.channel.send(message.content)
    
    # Uwu Logic
    if bot.uwu_target == uid:
        uwu_map = str.maketrans({'r': 'w', 'l': 'w', 'R': 'W', 'L': 'W'})
        await message.channel.send(f"{message.content.translate(uwu_map)} uwu")

# ─── UI ENGINE (BOXED STYLE) ───
def ui_box(title, body, footer="Made by purge"):
    width = 34
    header = (
        f"[1;30m╭{'─'*(width-2)}╮[0m\n"
        f"[1;31m Category:[0m [1;37m{title}[0m\n"
        f"[1;31m Commands:[0m [1;30m{bot.command_prefix}help <cat>[0m\n"
        f"[1;30m├{'─'*(width-2)}┤[0m\n"
    )
    content = ""
    for line in body.split("\n"):
        content += f" {line}\n"
    
    foot = (f"[1;30m├{'─'*(width-2)}┤[0m\n" f" [1;31m {footer}[0m\n")
    close = f"[1;30m╰{'─'*(width-2)}╯[0m"
    return f"```ansi\n{header}{content}{foot}{close}\n```"

# ─── MDM COMMAND ───

@bot.command()
async def mdm(ctx, *, content: str = None):
    """Mass DM with random delay and placeholder support"""
    template = content if content else DEFAULT_TEMPLATE
    
    if "<ping>" not in template and "<user>" not in template:
        return await ctx.send(ui_box("MDM Error", "[1;31mMissing Tags![0m\nUse [1;37m<ping>[0m or [1;37m<user>[0m"), delete_after=10)

    status_msg = await ctx.send(ui_box("MDM Scan", "[1;33mSearching servers...[0m"))
    await ctx.message.delete()

    targets = set()
    for guild in bot.guilds:
        for member in guild.members:
            if member.bot or member == bot.user or member.id in MDM_BLACKLIST:
                continue
            targets.add(member)

    if not targets:
        return await status_msg.edit(content=ui_box("MDM Error", "[1;31mNo users found.[0m"))

    targets = list(targets)
    random.shuffle(targets) # Stealth: Randomize order
    sent, failed = 0, 0

    for member in targets:
        try:
            # Name Logic: Nickname > Global > Username
            name = member.display_name or member.global_name or member.name
            msg = template.replace("<ping>", member.mention).replace("<user>", name)
            
            await member.send(msg)
            sent += 1
            
            if sent % 3 == 0: # Update UI progress every 3 messages
                await status_msg.edit(content=ui_box("MDM Running", f"[1;32mSent: {sent}[0m\n[1;31mFailed: {failed}[0m\n[1;30mLast: {name}[0m"))
                
        except discord.HTTPException as e:
            failed += 1
            if e.code == 429: # Rate limit handling
                await status_msg.edit(content=ui_box("MDM Pause", "[1;33mRate Limit - Sleeping 60s[0m"))
                await asyncio.sleep(60)
        except:
            failed += 1

        # Protective Jitter
        await asyncio.sleep(BASE_DELAY + random.uniform(JITTER_MIN, JITTER_MAX))

    await status_msg.edit(content=ui_box("MDM Finish", f"[1;32mSent: {sent}[0m\n[1;31mFailed: {failed}[0m"))

# ─── HELP & CATEGORIES ───

@bot.command()
async def help(ctx, cat=None):
    if not cat:
        body = (
            "[1;37mStatus  [1;31m|[0m [1;34mRPC & AFK commands[0m\n"
            "[1;37mSocial  [1;31m|[0m [1;34mReact & Troll commands[0m\n"
            "[1;37mUtility [1;31m|[0m [1;34mMisc & MDM commands[0m"
        )
        return await ctx.send(ui_box("Main Menu", body), delete_after=15)
    
    c = cat.lower()
    if c == "status":
        body = "[1;30m▸[0m `,rpc` `,streaming` `,afk` `,dot`"
        await ctx.send(ui_box("Status", body), delete_after=10)
    elif c == "social":
        body = "[1;30m▸[0m `,ar` `,mr` `,sr` `,rl` `,uwu` `,mock`"
        await ctx.send(ui_box("Social", body), delete_after=10)
    elif c == "utility":
        body = "[1;30m▸[0m `,spam` `,purge` `,ping` `,mdm`"
        await ctx.send(ui_box("Utility", body), delete_after=10)

# ─── OTHER COMMANDS ───

@bot.command()
async def rpc(ctx, mode, *, text):
    m = mode.lower()
    if m == "play": act = discord.Game(name=text)
    elif m == "listen": act = discord.Activity(type=discord.ActivityType.listening, name=text)
    elif m == "watch": act = discord.Activity(type=discord.ActivityType.watching, name=text)
    else: return
    await bot.change_presence(activity=act)
    await ctx.send(ui_box("Presence", f"[1;36m{m.upper()}ING[0m | [1;37m{text}[0m"), delete_after=3)

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args):
    try:
        user = ctx.message.mentions[0]
        emojis = args.replace(f"<@{user.id}>", "").replace(f"<@!{user.id}>", "").strip().split()
        bot.targets[user.id] = emojis
        await ctx.send(ui_box("AR Add", f"[1;34mTarget:[0m {user.name}\n[1;34mReacts:[0m {' '.join(emojis)}"), delete_after=5)
    except: pass

@bot.command(aliases=['mr'])
async def multireact(ctx, *, args):
    try:
        if ctx.message.reference:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            user = ref.author
            emojis = args.split()
        else:
            user = ctx.message.mentions[0]
            emojis = args.replace(f"<@{user.id}>", "").replace(f"<@!{user.id}>", "").strip().split()
        bot.targets[user.id] = emojis
        await ctx.send(ui_box("Multi", f"[1;32mFollowing:[0m {user.name}\n[1;32mEmojis:[0m {' '.join(emojis)}"), delete_after=5)
    except: pass

@bot.command(aliases=['rl'])
async def reactlog(ctx):
    if not bot.targets: return await ctx.send("`[!]` No active tracks.", delete_after=5)
    body = ""
    for tid, emojis in bot.targets.items():
        u = bot.get_user(tid)
        name = u.name if u else tid
        body += f"[1;34m{name}[0m [1;30m|[0m {' '.join(emojis)}\n"
    await ctx.send(ui_box("React Log", body), delete_after=15)

@bot.command(aliases=['sr'])
async def stopreact(ctx, *, args=None):
    tid = None
    if not args and ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        tid = ref.author.id
    elif args and args.lower() == "all":
        bot.targets = {}
        return await ctx.send(ui_box("AR Clear", "[1;31mALL TARGETS REMOVED[0m"), delete_after=3)
    elif ctx.message.mentions:
        tid = ctx.message.mentions[0].id
    
    if tid and tid in bot.targets:
        bot.targets.pop(tid)
        await ctx.send(ui_box("AR Stop", f"[1;31mRemoved ID:[0m {tid}"), delete_after=3)

@bot.command()
async def ping(ctx):
    await ctx.send(ui_box("System", f"[1;32mLATENCY:[0m {int(bot.latency * 1000)}ms"), delete_after=5)

@bot.command()
async def stop(ctx):
    bot.spamming = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await ctx.send(ui_box("Halt", "[1;31mALL SYSTEMS STOPPED[0m"), delete_after=3)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))

