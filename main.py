import discord
import asyncio
import os
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── SYSTEM PULSE (KEEP-ALIVE for Replit / similar hosts) ───
app = Flask('')

@app.route('/')
def home():
    return "SYSTEM ONLINE"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

Thread(target=run_flask, daemon=True).start()

# ─── CONFIG ───
TOKEN = os.getenv("DISCORD_TOKEN")

hosted_sessions = {}

# ─── Kill Bot Class ───
class Kill(commands.Bot):
    def __init__(self, display_name="Main"):
        super().__init__(
            command_prefix="!",
            self_bot=True,
            help_command=None
        )
        self.display_name = display_name
        self.spamming = False
        self.dm_active = False
        self.react_emoji = None
        self.target_id = None
        self._process_lock = set()

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.display_name} ({self.user}) ───")

    async def on_message(self, message):
        # Auto-react if configured
        if self.react_emoji:
            if message.author.id == self.target_id or \
               (self.target_id == self.user.id and message.author.id == self.user.id):
                asyncio.create_task(message.add_reaction(self.react_emoji))

        # Only process commands from ourselves (self-bot behavior)
        if message.author.id != self.user.id:
            return

        if message.content.startswith("!"):
            if message.id in self._process_lock:
                return
            self._process_lock.add(message.id)
            await self.process_commands(message)
            self._process_lock.discard(message.id)


# ─── Fancy UI message ───
async def ui_send(ctx, title, body, color="34"):
    ui = (
        f"```ansi\n"
        f"[1;{color}m[ {title} ][0m\n"
        f"[1;30m────────────────────────────────[0m\n"
        f"{body}\n"
        f"[1;30m────────────────────────────────[0m\n"
        f"[1;31mSPEED: UNLEASHED[0m\n"
        f"```"
    )
    asyncio.create_task(ctx.send(ui, delete_after=4))


# ─── Register all commands ───
def add_commands(bot: Kill):

    @bot.command()
    async def host(ctx, token: str, *, name: str):
        await ctx.message.delete()
        new_bot = Kill(display_name=name)
        add_commands(new_bot)
        asyncio.create_task(new_bot.start(token))
        hosted_sessions[name] = new_bot
        await ui_send(ctx, "HOST", f"Started: {name}", "32")


    @bot.command()
    async def unhost(ctx, *, name: str):
        await ctx.message.delete()
        if name in hosted_sessions:
            await hosted_sessions.pop(name).close()
            await ui_send(ctx, "HOST", f"Killed: {name}", "31")


    @bot.command()
    async def listhosted(ctx):
        await ctx.message.delete()
        body = "\n".join([f"• {n}" for n in hosted_sessions.keys()]) if hosted_sessions else "None"
        await ui_send(ctx, "HOSTS", body, "34")


    @bot.command()
    async def help(ctx):
        await ctx.message.delete()
        body = (
            "!spam [n] [m]     | !purge [n]\n"
            "!av [@u]          | !ping\n"
            "!mdm [m]          | !host [t] [n]\n"
            "!listhosted       | !rpc [type] [txt]\n"
            "!stop"
        )
        await ui_send(ctx, "KILL", body, "35")


    @bot.command()
    async def spam(ctx, amount: int, *, text):
        await ctx.message.delete()
        bot.spamming = True
        for _ in range(amount):
            if not bot.spamming:
                break
            asyncio.create_task(ctx.send(text))
            await asyncio.sleep(0.005)
        bot.spamming = False


    @bot.command()
    async def purge(ctx, amount: int):
        await ctx.message.delete()
        count = 0
        async for m in ctx.channel.history(limit=1000):
            if m.author.id == bot.user.id:
                try:
                    asyncio.create_task(m.delete())
                    count += 1
                    await asyncio.sleep(0.005)
                except:
                    continue
            if count >= amount:
                break
        await ui_send(ctx, "PURGE", f"Wiped {count}", "34")


    @bot.command()
    async def mdm(ctx, *, msg):
        await ctx.message.delete()
        await ui_send(ctx, "MDM", "1: DMs | 2: Friends | 3: All", "33")

        try:
            reply = await bot.wait_for(
                'message',
                check=lambda m: m.author.id == bot.user.id and m.content in '123',
                timeout=15
            )
            choice = reply.content

            if choice == '2':
                targets = list(bot.user.friends)
            elif choice == '1':
                targets = [r.recipient for r in bot.private_channels if isinstance(r, discord.DMChannel)]
            else:  # 3
                dm_users = [r.recipient for r in bot.private_channels if isinstance(r, discord.DMChannel)]
                targets = list(set(bot.user.friends + dm_users))

            bot.dm_active = True
            for target in targets:
                if not bot.dm_active or target.id == bot.user.id:
                    continue
                try:
                    await target.send(msg)
                    await asyncio.sleep(3.0)
                except:
                    pass
            bot.dm_active = False

        except asyncio.TimeoutError:
            pass


    @bot.command()
    async def rpc(ctx, rpc_type: str, *, text: str):
        await ctx.message.delete()

        t_map = {
            "playing":   discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching":  discord.ActivityType.watching,
        }

        if rpc_type.lower() == "spotify":
            activity = discord.Spotify(title=text, artist="KILL")
        else:
            activity = discord.Activity(
                type=t_map.get(rpc_type.lower(), discord.ActivityType.playing),
                name=text,
                url="https://twitch.tv/" if rpc_type.lower() == "streaming" else None
            )

        await bot.change_presence(activity=activity)
        await ui_send(ctx, "RPC", f"Set: {rpc_type}", "35")


    @bot.command()
    async def stop(ctx):
        await ctx.message.delete()
        bot.spamming = False
        bot.dm_active = False
        await ui_send(ctx, "STOP", "Halted", "31")


# ─── Create & run main bot ───
if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
    else:
        master_bot = Kill()
        add_commands(master_bot)
        master_bot.run(TOKEN)
