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
bot.targets = {}       
bot.spamming = False
bot.mock_target = None
bot.status_messages = []
bot.rotating_status = False

@bot.event
async def on_ready():
    print(f"─── {bot.user} v6.0 TURBO ACTIVE ───")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    author_id = int(message.author.id)
    
    if author_id in bot.targets:
        if not message.content.startswith(","):
            for e in bot.targets[author_id]:
                try: 
                    await message.add_reaction(e.strip())
                    await asyncio.sleep(0.05) # Half-speed buffer for sticking
                except: pass

    if author_id != int(bot.user.id) and bot.mock_target == author_id:
        await message.channel.send("".join([c.upper() if i%2==0 else c.lower() for i,c in enumerate(message.content)]))

def ui(color, title, text):
    # Faster delete_after on UI boxes (6 seconds instead of 10)
    return f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{text}\n[1;30m┗━━━━━━━━━━━━━━━━┛[0m\n```"

# ─── UPDATED HELP SYSTEM ───

@bot.command()
async def help(ctx, cat=None):
    if not cat:
        body = "[1;34m,help status[0m\n[1;35m,help social[0m\n[1;31m,help utility[0m"
        return await ctx.send(ui("37", "HELP MENU", body), delete_after=6)
    
    c = cat.lower()
    if c == "status":
        body = "`,addstatus [text]` | `,rotatestatus [on/off]`\n`,rpc [text]` | `,dot [online/idle/dnd]`\n`,clearstatus`"
        await ctx.send(ui("35", "STATUS COMMANDS", body), delete_after=8)
    elif c == "social":
        body = "`,ar @u [e]` | `,targets` | `,stopreact` | `,mock @u`"
        await ctx.send(ui("36", "SOCIAL COMMANDS", body), delete_after=8)
    elif c == "utility":
        body = "`,spam [n] [t]` | `,purge [n]` | `,stop` | `,ping`"
        await ctx.send(ui("31", "UTILITY COMMANDS", body), delete_after=8)

# ─── TURBO STATUS COMMANDS ───

@bot.command()
async def dot(ctx, mode):
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    status = modes.get(mode.lower(), discord.Status.online)
    await bot.change_presence(status=status)
    await ctx.send(ui("32", "STATUS", f"Mode set to: {mode.upper()}"), delete_after=3)

@bot.command()
async def addstatus(ctx, *, t):
    bot.status_messages.append(t)
    await ctx.send(ui("35", "STATUS", f"Added: {t}"), delete_after=3)

@bot.command()
async def rotatestatus(ctx, toggle):
    bot.rotating_status = (toggle.lower() == "on")
    if bot.rotating_status:
        async def s_loop():
            while bot.rotating_status:
                for t in bot.status_messages:
                    if not bot.rotating_status: break
                    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name="x", state=t))
                    await asyncio.sleep(10) # Speed of rotation
        bot.loop.create_task(s_loop())
    await ctx.send(ui("32", "ROTATION", f"Status Rotation: {toggle.upper()}"), delete_after=3)

@bot.command()
async def clearstatus(ctx):
    bot.status_messages = []
    bot.rotating_status = False
    await bot.change_presence(activity=None)
    await ctx.send(ui("31", "STATUS", "Cleared all presence."), delete_after=3)

@bot.command()
async def rpc(ctx, *, t):
    await bot.change_presence(activity=discord.Game(name=t))
    await ctx.send(ui("34", "RPC", f"Now Playing: {t}"), delete_after=3)

# ─── TURBO UTILITY ───

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    count = 0
    async for m in ctx.channel.history(limit=n + 10):
        if m.author.id == bot.user.id:
            try: 
                await m.delete()
                count += 1
                if count >= n: break
                await asyncio.sleep(0.02) # Ultra-fast purge
            except: pass

@bot.command()
async def spam(ctx, n: int, *, t):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(t)
        await asyncio.sleep(0.3) # Slightly faster spam

# ─── AR ENGINE (NAMED) ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
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
        await ctx.send(ui("32", "AR ADDED", f"Target: {target.name}\nTotal: {len(bot.targets)}"), delete_after=4)
    else:
        await ctx.send("User not found.", delete_after=3)

@bot.command()
async def stopreact(ctx, *, args=None):
    if args and "all" in args.lower():
        bot.targets = {}
        return await ctx.send(ui("31", "AR", "Registry Wiped."), delete_after=3)
    
    tid = None
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        tid = int(ref.author.id)
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m: tid = int(id_m.group())

    if tid and tid in bot.targets:
        bot.targets.pop(tid)
        await ctx.send(ui("31", "AR", f"Removed: {tid}"), delete_after=3)

@bot.command()
async def targets(ctx):
    if not bot.targets: return await ctx.send(ui("34", "AR", "Empty."), delete_after=5)
    lines = [f"[1;34m{(bot.get_user(tid).name if bot.get_user(tid) else tid)}[0m: {' '.join(emojis)}" for tid, emojis in bot.targets.items()]
    await ctx.send(ui("34", "REGISTRY", "\n".join(lines)), delete_after=10)

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_status = False
    bot.targets = {}; bot.mock_target = None
    await ctx.send(ui("31", "HALT", "All tasks killed."), delete_after=3)

@bot.command()
async def ping(ctx):
    await ctx.send(ui("32", "PONG", f"{round(bot.latency * 1000)}ms"), delete_after=3)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
