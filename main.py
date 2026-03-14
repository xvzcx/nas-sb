import discord, asyncio, os, re, time, requests
from discord.ext import commands
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"
def run(): app.run(host='0.0.0.0', port=8080)

# We use the simplest possible setup to ensure the bot actually responds
bot = commands.Bot(command_prefix=",", self_bot=True, help_command=None)

# Global Storage
bot.spamming = False
bot.targets = {} # {user_id: [emojis]}

@bot.event
async def on_ready():
    print(f"─── {bot.user} ONLINE ───")

@bot.event
async def on_message(message):
    # 1. ALWAYS process commands first
    await bot.process_commands(message)

    # 2. Check targets (Dictionary check)
    if message.author.id in bot.targets:
        if not message.content.startswith(","):
            for emoji in bot.targets[message.author.id]:
                try: await message.add_reaction(emoji.strip())
                except: pass

def ui(color, title, text):
    return f"```ansi\n[1;{color}m┏━ [ {title} ] ━┓[0m\n{text}\n[1;30m┗━ v4.8 ━┛[0m\n```"

# ─── THE AR COMMANDS ───

@bot.command(aliases=['ar'])
async def autoreact(ctx, *, args=None):
    target_id = None
    
    if ctx.message.reference:
        msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        target_id = msg.author.id
        emojis = args.split() if args else ["🔥"]
    elif args:
        if "me" in args.lower():
            target_id = bot.user.id
            emojis = args.lower().replace("me", "").split()
        else:
            id_match = re.search(r'\d+', args)
            if id_match:
                target_id = int(id_match.group())
                # Remove the ID/Mention from the string to get just emojis
                clean_args = re.sub(r'<@!?\d+>', '', args).strip()
                emojis = clean_args.split()
        
        if not emojis: emojis = ["🔥"]
    
    if target_id:
        bot.targets[target_id] = emojis
        await ctx.send(ui("32", "AR ADDED", f"ID: {target_id}\nEmojis: {' '.join(emojis)}"))
    else:
        await ctx.send("**[ERROR]** Mention someone or reply.")

@bot.command()
async def stopreact(ctx, *, args=None):
    if args and "all" in args.lower():
        bot.targets = {}
        await ctx.send(ui("31", "AR", "Cleared all targets."))
    else:
        # Default to removing person you replied to or mentioned
        id_match = re.search(r'\d+', args) if args else None
        target_id = int(id_match.group()) if id_match else None
        if not target_id and ctx.message.reference:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            target_id = msg.author.id
            
        if target_id in bot.targets:
            del bot.targets[target_id]
            await ctx.send(ui("31", "AR", f"Removed {target_id}"))

@bot.command()
async def targets(ctx):
    if not bot.targets:
        return await ctx.send(ui("34", "TARGETS", "None active."))
    t_list = "\n".join([f"{k}: {' '.join(v)}" for k, v in bot.targets.items()])
    await ctx.send(ui("34", "ACTIVE LIST", t_list))

# ─── UTILS ───

@bot.command()
async def spam(ctx, n: int, *, text):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(text)
        await asyncio.sleep(0.4)

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
    await ctx.send(ui("31", "HALT", "Everything stopped."))

@bot.command()
async def ping(ctx):
    await ctx.send(ui("32", "PONG", f"{round(bot.latency * 1000)}ms"))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
