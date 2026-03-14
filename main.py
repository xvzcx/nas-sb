import discord, asyncio, os, re, time, requests
from discord.ext import commands
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.route('/')
def home(): return "ONLINE"
def run(): app.run(host='0.0.0.0', port=8080)

class Kill(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.spamming = False
        self.mock_target = self.uwu_target = self.react_target_id = None
        self.react_emojis = []
        self.afk_reason = None
        self.afk_time = 0
        self.status_dot = discord.Status.online
        self.bio_msgs = []
        self.status_msgs = []
        self.rotating_bio = self.rotating_status = False

    async def on_ready(self): print(f"Logged in as {self.user}")

    async def on_message(self, msg):
        if msg.author.id == self.user.id:
            await self.process_commands(msg)
            if self.afk_reason and not msg.content.startswith(","):
                if (time.time() - self.afk_time) > 5:
                    self.afk_reason = None
                    await msg.channel.send("```ansi\n[1;32m[AFK OFF][0m```", delete_after=5)
        elif self.react_target_id == msg.author.id:
            for e in self.react_emojis:
                try: await msg.add_reaction(e)
                except: pass
        if self.mock_target == msg.author.id:
            await msg.channel.send("".join([c.upper() if i%2==0 else c.lower() for i,c in enumerate(msg.content)]))
        if self.uwu_target == msg.author.id:
            await msg.channel.send(msg.content.replace('r','w').replace('l','w')+" uwu")
        if self.afk_reason and self.user.mentioned_in(msg):
            await msg.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=5)

bot = Kill()

def ui(color, title, text): # Manual ANSI UI
    return f"```ansi\n[1;{color}m[{title}][0m {text}```"

@bot.command()
async def ping(ctx): await ctx.send(ui("32", "PONG", f"{round(bot.latency*1000)}ms"))

@bot.command()
async def dot(ctx, m):
    modes = {"online": discord.Status.online, "dnd": discord.Status.dnd, "idle": discord.Status.idle}
    bot.status_dot = modes.get(m.lower(), discord.Status.online)
    await bot.change_presence(status=bot.status_dot)
    await ctx.send(ui("34", "DOT", m.upper()))

@bot.command()
async def rpc(ctx, *, t):
    await bot.change_presence(activity=discord.Game(name=t), status=bot.status_dot)
    await ctx.send(ui("34", "RPC", t))

@bot.command()
async def mock(ctx, *, a):
    bot.mock_target = int(''.join(filter(str.isdigit, a)))
    await ctx.send(ui("31", "MOCK", f"Target: {bot.mock_target}"))

@bot.command()
async def uwu(ctx, *, a):
    bot.uwu_target = int(''.join(filter(str.isdigit, a)))
    await ctx.send(ui("35", "UWU", f"Target: {bot.uwu_target}"))

@bot.command()
async def unmock(ctx):
    bot.mock_target = bot.uwu_target = None
    await ctx.send(ui("31", "TROLL", "Disabled"))

@bot.command()
async def addstatus(ctx, *, t):
    bot.status_msgs.append(t)
    await ctx.send(ui("35", "STATUS", f"Added. Total: {len(bot.status_msgs)}"))

@bot.command()
async def rotatestatus(ctx, m):
    bot.rotating_status = m.lower() == "on"
    if bot.rotating_status:
        async def loop():
            while bot.rotating_status:
                for s in bot.status_msgs:
                    await bot.change_presence(activity=discord.CustomActivity(name=s), status=bot.status_dot)
                    await asyncio.sleep(12)
        bot.loop.create_task(loop())
    await ctx.send(ui("35", "STATUS", f"Rotation: {m.upper()}"))

@bot.command()
async def addbio(ctx, *, t):
    bot.bio_msgs.append(t)
    await ctx.send(ui("32", "BIO", "Added."))

@bot.command()
async def rotatebio(ctx, m):
    bot.rotating_bio = m.lower() == "on"
    if bot.rotating_bio:
        async def loop():
            while bot.rotating_bio:
                for b in bot.bio_msgs:
                    requests.patch("https://discord.com/api/v9/users/@me", headers={"Authorization": os.getenv("DISCORD_TOKEN")}, json={"bio": b})
                    await asyncio.sleep(45)
        bot.loop.create_task(loop())
    await ctx.send(ui("32", "BIO", f"Rotation: {m.upper()}"))

@bot.command()
async def spam(ctx, n: int, *, t):
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        await ctx.send(t); await asyncio.sleep(1.1)

@bot.command()
async def multireact(ctx, *, a):
    parts = a.split()
    bot.react_target_id = int(''.join(filter(str.isdigit, parts[0])))
    bot.react_emojis = parts[1:4]
    await ctx.send(ui("36", "REACT", f"Locked: {bot.react_target_id}"))

@bot.command()
async def stopreact(ctx):
    bot.react_target_id = None
    await ctx.send(ui("31", "REACT", "Stopped"))

@bot.command()
async def afk(ctx, *, r="Away"):
    bot.afk_reason, bot.afk_time = r, time.time()
    await ctx.send(ui("33", "AFK", r))

@bot.command()
async def purge(ctx, n: int):
    await ctx.message.delete()
    async for m in ctx.channel.history(limit=n):
        if m.author.id == bot.user.id:
            try: await m.delete()
            except: pass
            await asyncio.sleep(0.2)

@bot.command()
async def stop(ctx):
    bot.spamming = bot.rotating_bio = bot.rotating_status = False
    bot.mock_target = bot.uwu_target = bot.react_target_id = None
    await ctx.send(ui("31", "HALT", "Everything stopped."))

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run(os.getenv("DISCORD_TOKEN"))
