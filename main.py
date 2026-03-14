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
bot.targets = {}       # {int(user_id): [emojis]}
bot.spamming = False
bot.mock_target = None
bot.uwu_target = None
bot.afk_reason = None
bot.status_messages = []
bot.rotating_status = False

@bot.event
async def on_ready():
    print(f"─── {bot.user} v5.7 READY ───")

@bot.event
async def on_message(message):
    # Process commands first
    await bot.process_commands(message)

    # ─── THE MULTI-STICK LOGIC ───
    # We check if the author ID (as an integer) is in our hitlist
    uid = message.author.id
    if uid in bot.targets:
        # Ignore your own commands so the AR doesn't clutter the chat
        if not message.content.startswith(","):
            emojis = bot.targets[uid]
            for e in emojis:
                try:
                    await message.add_reaction(e.strip())
                    await asyncio.sleep(0.1) # Small buffer to ensure they "stick"
                except:
                    continue

    # Trolling Logic (Others only)
    if message.author.id != bot.user.id:
        if bot.mock_target == message.author.id:
            await message.channel.send("".join([c.upper() if i%2==0 else c.lower() for i,c in enumerate(message.content)]))

def ui(color, title, text):
    return f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{text}\n[1;30m┗━━ v5.7 ━━┛[0m\n```"

# ─── REBUILT AR COMMANDS ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
    target_id = None
    
    # 1. Check for Reply
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target_id = int(ref.author.id)
        raw_emojis = args if args else "🔥"
    # 2. Check for "me" or @mentions
    elif args:
        if "me" in args.lower():
            target_id = int(bot.user.id)
            raw_emojis = args.lower().replace("me", "").strip()
        else:
            id_m = re.search(r'\d+', args)
            if id_m:
                target_id = int(id_m.group())
                raw_emojis = re.sub(r'<@!?\d+>', '', args).strip()

    if target_id:
        # Convert emoji string to list, default to fire if empty
        emojis = raw_emojis.split() if raw_emojis else ["🔥"]
        # Force integer key in dictionary
        bot.targets[int(target_id)] = emojis 
        await ctx.send(ui("32", "AR ADDED", f"ID: {target_id}\nEmojis: {' '.join(emojis)}\nTotal Active: {len(bot.targets)}"))
    else:
        await ctx.send(ui("31", "ERROR", "Reply to someone or @mention them."))

@bot.command()
async def targets(ctx):
    """View all current AR targets"""
    if not bot.targets:
        return await ctx.send(ui("34", "AR LIST", "Registry is empty."))
    
    body = "\n".join([f"[1;34m{k}[0m: {' '.join(v)}" for k, v in bot.targets.items()])
    await ctx.send(ui("34", "ACTIVE REGISTRY", body))

@bot.command()
async def stopreact(ctx, *, args=None):
    """,stopreact @user OR ,stopreact all"""
    if args and "all" in args.lower():
        bot.targets = {}
        return await ctx.send(ui("31", "AR", "Registry cleared."))
    
    target_id = None
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target_id = ref.author.id
    elif args:
        id_m = re.search(r'\d+', args)
        if id_m: target_id = int(id_m.group())
        
    if target_id in bot.targets:
        del bot.targets[target_id]
        await ctx.send(ui("31", "AR", f"Removed {target_id}"))

# ─── CORE UTILITY ───

@bot.command()
async def help(ctx, cat=None):
    if not cat:
        body = "[1;34m,help status[0m\n[1;35m,help social[0m\n[1;31m,help utility[0m"
        return await ctx.send(ui("37", "HELP MENU", body))
    
    c = cat.lower()
    if c == "social":
        body = "`,ar @u [e]` | `,targets` | `,stopreact` | `,mock @u`"
        await ctx.send(ui("36", "SOCIAL", body))
    elif c == "utility":
        body = "`,spam [n] [t]` | `,purge [n]` | `,afk [r]` | `,stop`"
        await ctx.send(ui("31", "UTILITY", body))

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for m in ctx.channel.history(limit=n):
        if m.author.id == bot.user.id:
            try: await m.delete(); await asyncio.sleep(0.05)
            except: pass

@bot.command()
async def stop(ctx):
    bot.spamming = False
    bot.targets = {}
    bot.mock_target = None
    await ctx.send(ui("31", "HALT", "All targets and tasks wiped."))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
