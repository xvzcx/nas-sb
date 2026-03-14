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
bot.status_messages = []
bot.rotating_status = False

@bot.event
async def on_ready():
    print(f"─── {bot.user} v6.4 STABLE ACTIVE ───")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    uid = int(message.author.id)
    
    # 1. AFK LOGIC (SELF-OFF)
    if message.author.id == bot.user.id:
        # FIX: Only disable AFK if the message is NOT a command
        if bot.afk_reason and not message.content.startswith(bot.command_prefix):
            bot.afk_reason = None
            await message.channel.send("`[AFK]` Disabled. Welcome back.", delete_after=3)
        return

    # 2. AFK PING RESPONDER
    if bot.afk_reason and bot.user.mentioned_in(message):
        await message.channel.send(f"**[AFK]** {bot.afk_reason}", delete_after=5)

    # 3. MULTI-STICK AR
    if uid in bot.targets:
        if not message.content.startswith(bot.command_prefix):
            for e in bot.targets[uid]:
                try: 
                    await message.add_reaction(e.strip())
                    await asyncio.sleep(0.05) 
                except: pass

    # 4. TROLLING
    if uid != int(bot.user.id):
        if bot.mock_target == uid:
            await message.channel.send("".join([c.upper() if i%2==0 else c.lower() for i,c in enumerate(message.content)]))
        if bot.uwu_target == uid:
            uwu_text = message.content.replace('r','w').replace('l','w').replace('R','W').replace('L','W')
            await message.channel.send(f"{uwu_text} uwu")

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

# ─── UPDATED STATUS PAGE ───

@bot.command()
async def help(ctx, cat=None):
    if not cat:
        body = "[1;34m» ,help status[0m\n[1;35m» ,help social[0m\n[1;31m» ,help utility[0m"
        return await ctx.send(ui("37", "MAIN MENU", body), delete_after=6)
    
    c = cat.lower()
    if c == "status":
        body = "[1;30m▸[0m `,afk [reason]` [1;30m▸[0m `,rpc`\n[1;30m▸[0m `,addstatus`    [1;30m▸[0m `,dot`\n[1;30m▸[0m `,rotatestatus` [1;30m▸[0m `,clearstatus`"
        await ctx.send(ui("34", "STATUS", body), delete_after=8)
    elif c == "social":
        body = "[1;30m▸[0m `,ar @u [e]`  [1;30m▸[0m `,targets`\n[1;30m▸[0m `,stopreact`  [1;30m▸[0m `,mock @u`\n[1;30m▸[0m `,uwu @u`      [1;30m▸[0m `,stop`"
        await ctx.send(ui("35", "SOCIAL", body), delete_after=8)
    elif c == "utility":
        body = "[1;30m▸[0m `,spam [n] [t]` [1;30m▸[0m `,purge [n]`\n[1;30m▸[0m `,stop`         [1;30m▸[0m `,ping`"
        await ctx.send(ui("31", "UTILITY", body), delete_after=8)

# ─── CORE COMMANDS ───

@bot.command()
async def afk(ctx, *, reason="Away"):
    bot.afk_reason = reason
    await ctx.send(ui("33", "AFK", f"Status: [1;33mENABLED[0m\nReason: {reason}"), delete_after=5)

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    count = 0
    async for m in ctx.channel.history(limit=n + 5):
        if m.author.id == bot.user.id:
            try: 
                await m.delete()
                count += 1
                if count >= n: break
                await asyncio.sleep(0.02) 
            except: pass

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_status = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await ctx.send(ui("31", "HALT", "[1;31mAll tasks killed.[0m"), delete_after=3)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
