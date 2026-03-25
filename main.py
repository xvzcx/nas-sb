import discord, asyncio, os, re, time, requests, random
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── KEEPALIVE ENGINE ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"
def run_flask(): app.run(host='0.0.0.0', port=8080)

# Use self_bot=True for user account tokens
bot = commands.Bot(command_prefix=",", self_bot=True, help_command=None)

# --- GLOBAL REGISTRIES ---
bot.targets = {}       
bot.spamming = False
bot.mock_target = None
bot.uwu_target = None
bot.afk_reason = None
bot.afk_log = [] 
bot.current_rpc = None 
bot.rotating = False

@bot.event
async def on_ready():
    print(f"─── {bot.user} | Connection Established ───")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.content.startswith(bot.command_prefix): return
    uid = message.author.id

    # Autoreact
    if uid in bot.targets:
        for emoji in bot.targets[uid]:
            try: await message.add_reaction(emoji.strip())
            except: continue

    # Self-logic (AFK toggle)
    if uid == bot.user.id:
        if bot.afk_reason and "┎" not in message.content:
            bot.afk_reason = None
            await message.channel.send("`[AFK]` Disabled. Welcome back.", delete_after=3)
        return 
    
    # AFK Logger
    if bot.afk_reason and bot.user.mentioned_in(message) and not message.mention_everyone:
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        bot.afk_log.append(f"[1;30m[{timestamp}][0m [1;34m{message.author.name}[0m in #{message.channel}")
        await message.channel.send(f"**[AFK]** {bot.afk_reason}", delete_after=5)

    # Social Mock/Uwu
    if bot.mock_target == uid: await message.channel.send(message.content)
    if bot.uwu_target == uid:
        uwu_map = str.maketrans({'r': 'w', 'l': 'w', 'R': 'W', 'L': 'W'})
        await message.channel.send(f"{message.content.translate(uwu_map)} uwu")

# ─── UI ENGINE ───
def ui_box(title, body, color="31"):
    width = 32
    res = f"```ansi\n"
    res += f"[1;{color}m┎{'─'*(width-2)}┒[0m\n"
    res += f"[1;{color}m┃[0m [1;37m{title.center(width-4)}[0m [1;{color}m┃[0m\n"
    res += f"[1;{color}m┠{'─'*(width-2)}┨[0m\n"
    for line in body.split("\n"):
        res += f"[1;{color}m┃[0m {line.ljust(width-4)} [1;{color}m┃[0m\n"
    res += f"[1;{color}m┖{'─'*(width-2)}⚚[0m\n"
    res += "```"
    return res

# ─── STATUS & RPC ───

@bot.command()
async def customrpc(ctx, client_id, image_name, title, *, details):
    await ctx.message.delete()
    try:
        act = discord.Activity(
            type=discord.ActivityType.playing,
            application_id=int(client_id),
            name=title,
            details=details,
            assets={'large_image': image_name, 'large_text': title}
        )
        bot.current_rpc = act
        await bot.change_presence(activity=act)
        await ctx.send(ui_box("Dev RPC", f"Status: Active\nID: {client_id}", "36"), delete_after=5)
    except Exception as e: await ctx.send(f"Error: {e}", delete_after=5)

@bot.command()
async def streaming(ctx, title, *, details="Streaming"):
    await ctx.message.delete()
    act = discord.Streaming(name=title, details=details, url="https://twitch.tv/discord")
    bot.current_rpc = act
    await bot.change_presence(activity=act)
    await ctx.send(ui_box("Stream", f"Live: {title}", "35"), delete_after=3)

@bot.command()
async def afk(ctx, *, reason="Away"):
    await ctx.message.delete()
    bot.afk_reason = reason; bot.afk_log = []
    await ctx.send(ui_box("AFK", f"Status: ENABLED\nReason: {reason}", "33"), delete_after=5)

@bot.command()
async def afklog(ctx):
    await ctx.message.delete()
    if not bot.afk_log: return await ctx.send(ui_box("AFK Log", "No pings found.", "33"), delete_after=10)
    await ctx.send(ui_box("AFK Log", "\n".join(bot.afk_log[-8:]), "33"), delete_after=20)

@bot.command()
async def clearstatus(ctx):
    await ctx.message.delete()
    bot.current_rpc = None
    await bot.change_presence(activity=None)
    await ctx.send(ui_box("Status", "Cleared", "31"), delete_after=3)

# ─── FUN ENGINE ───

@bot.command()
async def dicksize(ctx, user: discord.Member = None):
    await ctx.message.delete()
    target = user or ctx.author
    size = random.randint(1, 15)
    await ctx.send(ui_box("Dick Size", f"[1;34m{target.name}[0m\n8{'='*size}D", "34"))

@bot.command()
async def gaymeter(ctx, user: discord.Member = None):
    await ctx.message.delete()
    target = user or ctx.author
    p = random.randint(1, 100)
    await ctx.send(ui_box("Gay Meter", f"[1;35m{target.name}[0m\n{p}% Gay 🏳️‍🌈", "35"))

@bot.command()
async def mock(ctx, user: discord.Member = None):
    await ctx.message.delete()
    bot.mock_target = user.id if user else None
    state = f"Targeting: {user.name}" if user else "Disabled"
    await ctx.send(ui_box("Mock", state, "31"), delete_after=5)

# ─── UTILITY ───

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
                await asyncio.sleep(0.1)
            except: continue

@bot.command()
async def help(ctx, cat=None):
    await ctx.message.delete()
    if not cat:
        body = "[1;32m» Status[0m\n[1;35m» Fun[0m\n[1;31m» Utility[0m"
        return await ctx.send(ui_box("Main Menu", body, "37"), delete_after=15)
    
    c = cat.lower()
    if c == "status":
        body = "[1;32m» customrpc[0m\n[1;32m» streaming[0m\n[1;32m» afk [reason][0m\n[1;32m» afklog[0m\n[1;32m» clearstatus[0m"
        color = "32"
    elif c == "fun":
        body = "[1;35m» dicksize[0m\n[1;35m» gaymeter[0m\n[1;35m» mock [@u][0m"
        color = "35"
    elif c == "utility":
        body = "[1;31m» purge [n][0m\n[1;31m» stop[0m"
        color = "31"
    else: return
    await ctx.send(ui_box(cat.title(), body, color), delete_after=15)

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        Thread(target=run_flask, daemon=True).start()
        try:
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            print("ERROR: Invalid Discord Token.")
