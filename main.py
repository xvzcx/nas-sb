import discord, asyncio, os, re, time, requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── KEEPALIVE ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# ─── BOT SETUP ───
bot = commands.Bot(command_prefix=",", self_bot=True, help_command=None)

# --- GLOBAL REGISTRIES ---
bot.targets = {}       # {user_id: [emojis]}
bot.spamming = False
bot.mock_target = None
bot.uwu_target = None
bot.afk_reason = None
bot.afk_pings = 0
bot.afk_log = []
bot.status_messages = []
bot.rotating_status = False
bot.bio_messages = []
bot.rotating_bio = False

@bot.event
async def on_ready():
    print(f"─── {bot.user} ULTIMATE ACTIVE ───")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    # 1. AFK Logic (Self)
    if message.author.id == bot.user.id:
        if bot.afk_reason and not message.content.startswith(","):
            bot.afk_reason = None # Auto-disable AFK on message
            await message.channel.send("`[AFK DISABLED]` Welcome back.", delete_after=3)
        return

    # 2. Multi-Target AR
    if message.author.id in bot.targets:
        if not message.content.startswith(","):
            for emoji in bot.targets[message.author.id]:
                try: await message.add_reaction(emoji.strip())
                except: pass

    # 3. Trolling Logic
    if bot.mock_target == message.author.id:
        await message.channel.send("".join([c.upper() if i%2==0 else c.lower() for i,c in enumerate(message.content)]))
    if bot.uwu_target == message.author.id:
        await message.channel.send(message.content.replace('r','w').replace('l','w')+" uwu")

    # 4. AFK Logging (Others mentioning you)
    if bot.afk_reason and bot.user.mentioned_in(message):
        bot.afk_pings += 1
        bot.afk_log.append(f"**{message.author}** in #{message.channel}")
        await message.channel.send(f"**[AFK]** {bot.afk_reason}", delete_after=5)

# ─── UI HELPER ───
def ui(color, title, text):
    return f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{text}\n[1;30m┗━━ v5.5 ━━┛[0m\n```"

# ─── AR COMMANDS ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
    target_id = None
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target_id, raw_emojis = ref.author.id, (args if args else "🔥")
    elif args:
        if "me" in args.lower():
            target_id, raw_emojis = bot.user.id, args.lower().replace("me", "").strip()
        else:
            id_m = re.search(r'\d+', args)
            if id_m:
                target_id = int(id_m.group())
                raw_emojis = re.sub(r'<@!?\d+>', '', args).strip()
    
    if target_id:
        bot.targets[target_id] = raw_emojis.split() if raw_emojis else ["🔥"]
        await ctx.send(ui("32", "AR ADDED", f"ID: {target_id}\nActive: {len(bot.targets)}"))
    else: await ctx.send("Mention or Reply.")

@bot.command()
async def stopreact(ctx, *, args=None):
    if args and "all" in args.lower(): bot.targets = {}
    elif ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        bot.targets.pop(ref.author.id, None)
    await ctx.send(ui("31", "AR", "Target(s) removed."))

@bot.command()
async def targets(ctx):
    if not bot.targets: return await ctx.send(ui("34", "AR", "Empty."))
    body = "\n".join([f"{k}: {' '.join(v)}" for k, v in bot.targets.items()])
    await ctx.send(ui("34", "REGISTRY", body))

# ─── ROTATORS & PROFILE ───

@bot.command()
async def addstatus(ctx, *, t):
    bot.status_messages.append(t)
    await ctx.send(ui("35", "STATUS", f"Added. Total: {len(bot.status_messages)}"))

@bot.command()
async def rotatestatus(ctx, toggle):
    bot.rotating_status = (toggle.lower() == "on")
    if bot.rotating_status:
        async def s_loop():
            while bot.rotating_status:
                for t in bot.status_messages:
                    if not bot.rotating_status: break
                    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name="x", state=t))
                    await asyncio.sleep(12)
        bot.loop.create_task(s_loop())
    await ctx.send(ui("32", "STATUS", f"Rotation: {toggle.upper()}"))

@bot.command()
async def rpc(ctx, *, t):
    await bot.change_presence(activity=discord.Game(name=t))
    await ctx.send(ui("34", "RPC", f"Playing: {t}"))

# ─── UTILITIES ───

@bot.command()
async def spam(ctx, n: int, *, t):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(t); await asyncio.sleep(0.4)

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for m in ctx.channel.history(limit=n):
        if m.author.id == bot.user.id:
            try: await m.delete(); await asyncio.sleep(0.05)
            except: pass

@bot.command()
async def afk(ctx, *, r="Away"):
    bot.afk_reason = r
    await ctx.send(ui("33", "AFK", f"Reason: {r}"))

@bot.command()
async def mock(ctx, *, args):
    id_m = re.search(r'\d+', args)
    if id_m: bot.mock_target = int(id_m.group())
    await ctx.send(ui("31", "MOCK", f"Target: {bot.mock_target}"))

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_status = bot.rotating_bio = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = None
    await ctx.send(ui("31", "HALT", "All tasks wiped."))

@bot.command()
async def help(ctx):
    menu = (
        "[1;34m,help social[0m | [1;35m,help util[0m\n"
        "[1;32m,ar @u [e][0m - Multi-AR\n"
        "[1;32m,targets[0m - List AR\n"
        "[1;33m,afk [r][0m - AFK System\n"
        "[1;31m,stop[0m - Kill all tasks"
    )
    await ctx.send(ui("37", "MAIN MENU", menu))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
