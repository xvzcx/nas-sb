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
    print(f"─── {bot.user} v7.0 OVERDRIVE ACTIVE ───")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    
    # ─── SELF-MESSAGE HANDLING ───
    if message.author.id == bot.user.id:
        if bot.afk_reason:
            if not message.content.startswith(bot.command_prefix) and "┏━" not in message.content and "**[AFK]**" not in message.content:
                bot.afk_reason = None
                await message.channel.send("`[AFK]` Disabled. Welcome back.", delete_after=3)
        return

    uid = int(message.author.id)

    # ─── STICKY AR ENGINE ───
    if uid in bot.targets:
        # Don't react to other commands
        if not message.content.startswith(bot.command_prefix):
            for emoji in bot.targets[uid]:
                try: 
                    await message.add_reaction(emoji.strip())
                    await asyncio.sleep(0.05) # Speed buffer for stability
                except:
                    pass

    # ─── SOCIAL TROLLING ───
    if bot.afk_reason and bot.user.mentioned_in(message) and not message.mention_everyone:
        await message.channel.send(f"**[AFK]** {bot.afk_reason}", delete_after=5)

    if bot.mock_target == uid:
        await message.channel.send("".join([c.upper() if i%2==0 else c.lower() for i,c in enumerate(message.content)]))
    
    if bot.uwu_target == uid:
        uwu_map = str.maketrans({'r': 'w', 'l': 'w', 'R': 'W', 'L': 'W'})
        await message.channel.send(f"{message.content.translate(uwu_map)} uwu")

# ─── NEAT UI ENGINE ───
def ui(color, title, text):
    line = "━━━━━━━━━━━━━━━━━━━━"
    return (
        f"```ansi\n"
        f"[1;{color}m┏━ {title.center(16)} ━┓[0m\n"
        f"{text}\n"
        f"[1;30m┗━{line[:len(title)+4]}━┛[0m\n"
        f"```"
    )

# ─── FIXED REACT COMMANDS ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
    """Add a target for AR. Usage: ,ar @user 🔥 or [Reply] ,ar 🔥"""
    target = None
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target, raw_emojis = ref.author, (args if args else "🔥")
    elif args:
        if "me" in args.lower():
            target, raw_emojis = bot.user, args.lower().replace("me", "").strip()
        else:
            id_match = re.search(r'\d+', args)
            if id_match:
                uid = int(id_match.group())
                target = bot.get_user(uid) or await bot.fetch_user(uid)
                raw_emojis = re.sub(r'<@!?\d+>', '', args).strip()

    if target:
        emojis = raw_emojis.split() if raw_emojis else ["🔥"]
        bot.targets[int(target.id)] = emojis 
        await ctx.send(ui("32", "AR ADDED", f"User: [1;32m{target.name}[0m\nReacts: {' '.join(emojis)}"), delete_after=4)
    else:
        await ctx.send(ui("31", "ERROR", "User not found."), delete_after=3)

@bot.command()
async def stopreact(ctx, *, args=None):
    """Remove target. Usage: ,stopreact @user, ,stopreact all, or [Reply]"""
    if args and "all" in args.lower():
        bot.targets = {}
        return await ctx.send(ui("31", "AR CLEARED", "All targets removed."), delete_after=3)
    
    tid = None
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        tid = int(ref.author.id)
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m: tid = int(id_m.group())

    if tid and tid in bot.targets:
        bot.targets.pop(tid)
        await ctx.send(ui("31", "AR REMOVED", f"Stopped reacting to: {tid}"), delete_after=3)
    else:
        await ctx.send(ui("31", "ERROR", "Target not found."), delete_after=3)

@bot.command()
async def targets(ctx):
    if not bot.targets: return await ctx.send(ui("34", "AR LIST", "Registry empty."), delete_after=5)
    
    lines = []
    for tid, emojis in bot.targets.items():
        user = bot.get_user(tid)
        name = user.name if user else tid
        lines.append(f"[1;30m•[0m [1;34m{name}[0m [1;30m»[0m {' '.join(emojis)}")
    
    await ctx.send(ui("34", "REGISTRY", "\n".join(lines)), delete_after=10)

# ─── UTILITY & HELP ───

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    count = 0
    async for m in ctx.channel.history(limit=n + 25):
        if m.author.id == bot.user.id:
            try: 
                await m.delete()
                count += 1
                if count >= n: break
                await asyncio.sleep(0.01) 
            except: pass

@bot.command()
async def spam(ctx, n: int, *, t):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(t)
        await asyncio.sleep(0.25)

@bot.command()
async def help(ctx, cat=None):
    if not cat:
        body = "[1;34m» ,help status[0m\n[1;35m» ,help social[0m\n[1;31m» ,help utility[0m"
        return await ctx.send(ui("37", "MAIN MENU", body), delete_after=6)
    
    c = cat.lower()
    if c == "status":
        body = "[1;30m▸[0m `,afk [r]`     [1;30m▸[0m `,afklog`\n[1;30m▸[0m `,addstatus`   [1;30m▸[0m `,dot`\n[1;30m▸[0m `,rotatestatus` [1;30m▸[0m `,clearstatus`"
        await ctx.send(ui("34", "STATUS", body), delete_after=8)
    elif c == "social":
        body = "[1;30m▸[0m `,ar @u [e]`  [1;30m▸[0m `,targets`\n[1;30m▸[0m `,stopreact`  [1;30m▸[0m `,mock @u`\n[1;30m▸[0m `,uwu @u`      [1;30m▸[0m `,stop`"
        await ctx.send(ui("35", "SOCIAL", body), delete_after=8)
    elif c == "utility":
        body = "[1;30m▸[0m `,spam [n] [t]` [1;30m▸[0m `,purge [n]`\n[1;30m▸[0m `,stop`         [1;30m▸[0m `,ping`"
        await ctx.send(ui("31", "UTILITY", body), delete_after=8)

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_status = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await ctx.send(ui("31", "HALT", "[1;31mAll tasks killed.[0m"), delete_after=3)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
