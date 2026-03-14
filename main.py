import discord, asyncio, os, re, time, requests
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── KEEPALIVE ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# ─── BOT SETUP (Minimalist for maximum compatibility) ───
bot = commands.Bot(command_prefix=",", self_bot=True, help_command=None)

# --- GLOBAL REGISTRIES ---
bot.targets = {}       # {int_id: [emoji_list]}
bot.spamming = False
bot.mock_target = None
bot.uwu_target = None
bot.afk_reason = None
bot.status_messages = []
bot.rotating_status = False

@bot.event
async def on_ready():
    print(f"─── {bot.user} v5.8 FULL ACCESS ───")

@bot.event
async def on_message(message):
    # Always process commands first to ensure responsiveness
    await bot.process_commands(message)

    # ─── UNIVERSAL AUTO-REACT ───
    # This works for ANY ID in the dictionary (Me or Others)
    if message.author.id in bot.targets:
        # Don't react to the setup commands to keep chat clean
        if not message.content.startswith(bot.command_prefix):
            for e in bot.targets[message.author.id]:
                try: 
                    await message.add_reaction(e.strip())
                    await asyncio.sleep(0.1) # Buffer to ensure it sticks
                except: 
                    pass

    # ─── TROLLING LOGIC ───
    if message.author.id != bot.user.id:
        if bot.mock_target == message.author.id:
            await message.channel.send("".join([c.upper() if i%2==0 else c.lower() for i,c in enumerate(message.content)]))
        if bot.uwu_target == message.author.id:
            await message.channel.send(message.content.replace('r','w').replace('l','w')+" uwu")

def ui(color, title, text):
    return f"```ansi\n[1;{color}m┏━━ [ {title} ] ━━┓[0m\n{text}\n[1;30m┗━━ v5.8 ━━┛[0m\n```"

# ─── FIXED MULTI-AR COMMAND ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
    target_id = None
    
    # 1. Reply Check
    if ctx.message.reference:
        ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target_id = int(ref.author.id)
        raw_emojis = args if args else "🔥"
    # 2. Mention/Me Check
    elif args:
        if "me" in args.lower():
            target_id = int(bot.user.id)
            raw_emojis = args.lower().replace("me", "").strip()
        else:
            id_match = re.search(r'\d+', args)
            if id_match:
                target_id = int(id_match.group())
                raw_emojis = re.sub(r'<@!?\d+>', '', args).strip()

    if target_id:
        emojis = raw_emojis.split() if raw_emojis else ["🔥"]
        bot.targets[target_id] = emojis 
        await ctx.send(ui("32", "AR ADDED", f"Target: {target_id}\nEmojis: {' '.join(emojis)}\nActive: {len(bot.targets)}"))
    else:
        await ctx.send(ui("31", "ERROR", "Reply or Mention someone."))

@bot.command()
async def targets(ctx):
    if not bot.targets: return await ctx.send(ui("34", "AR", "No active targets."))
    t_list = "\n".join([f"[1;34m{k}[0m: {' '.join(v)}" for k, v in bot.targets.items()])
    await ctx.send(ui("34", "REGISTRY", t_list))

@bot.command()
async def stopreact(ctx, *, args=None):
    if args and "all" in args.lower():
        bot.targets = {}
        return await ctx.send(ui("31", "AR", "Registry Wiped."))
    
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

# ─── CORE COMMANDS RESTORED ───

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
async def stop(ctx):
    bot.spamming = False
    bot.targets = {}; bot.mock_target = None
    await ctx.send(ui("31", "HALT", "Everything cleared."))

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
