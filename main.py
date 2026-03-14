import discord
import asyncio
import os
import re
import time
from discord.ext import commands
from flask import Flask
from threading import Thread

# ─── SYSTEM PULSE ───
app = Flask(__name__)
@app.route('/')
def home(): return "SYSTEM ONLINE"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ─── CONFIG ───
TOKEN = os.getenv("DISCORD_TOKEN")

# ─── Bot Class ───
class Kill(commands.Bot):
    def __init__(self, display_name="Main"):
        super().__init__(command_prefix=",", self_bot=True, help_command=None)
        self.display_name = display_name
        self.spamming = False
        self.target_id = None
        self.react_emoji = None
        self.afk_reason = None
        self.afk_time = 0
        # --- Status Text Rotator ---
        self.rotating_status = False
        self.status_messages = ["Hello", "Welcome", "To my profile"]
        self.status_dot = discord.Status.online

    async def on_ready(self):
        print(f"─── SESSION ACTIVE: {self.display_name} ({self.user}) ───")

    async def status_rotator(self):
        """Rotates the actual Custom Status text next to your name."""
        while self.rotating_status:
            for text in self.status_messages:
                if not self.rotating_status: break
                # This changes the actual Custom Status text
                await self.change_presence(
                    activity=discord.CustomActivity(name=text),
                    status=self.status_dot
                )
                await asyncio.sleep(5) # Changes every 5 seconds

    async def on_message(self, message):
        if self.afk_reason and self.user.mentioned_in(message) and message.author.id != self.user.id:
            try:
                await message.channel.send(f"**[AFK]** {self.afk_reason}", delete_after=10)
                return 
            except: pass

        if self.target_id and self.react_emoji and message.author.id == self.target_id:
            try: await message.add_reaction(self.react_emoji)
            except: pass
        
        if message.author.id == self.user.id:
            if message.content.startswith("**[AFK]**"): return
            if message.content.startswith(self.command_prefix):
                await self.process_commands(message)
                return
            if self.afk_reason:
                if (time.time() - self.afk_time) < 2: return
                self.afk_reason = None
                await ui_send(message.channel, "SYSTEM", "Welcome back! AFK removed.", "32")

# ─── UI Helper ───
async def ui_send(ctx, title, body, color="34"):
    ui = (f"```ansi\n[1;{color}m[ {title} ][0m\n"
          f"[1;30m────────────────────────────────[0m\n"
          f"{body}\n"
          f"[1;30m────────────────────────────────[0m\n```")
    dest = ctx.channel if hasattr(ctx, 'channel') else ctx
    await dest.send(ui, delete_after=5)

# ─── Command Registration ───
def add_commands(bot: Kill):
    @bot.command()
    async def help(ctx):
        body = (",dot [online/idle/dnd/inv]\n"
                ",addmsg [text] | ,clearmsgs\n"
                ",rotate [on/off]\n"
                ",afk [reason] | ,stop")
        await ui_send(ctx, "COMMANDS", body, "35")

    @bot.command()
    async def addmsg(ctx, *, text: str):
        """Add a message to the Status Text rotation."""
        bot.status_messages.append(text)
        await ui_send(ctx, "STATUS", f"Added: {text}", "32")

    @bot.command()
    async def clearmsgs(ctx):
        """Wipe the Status Text list."""
        bot.status_messages = []
        bot.rotating_status = False
        await ui_send(ctx, "STATUS", "List cleared.", "31")

    @bot.command()
    async def rotate(ctx, toggle: str):
        """Toggle the Custom Status text rotation."""
        if toggle.lower() == "on":
            if not bot.status_messages:
                return await ui_send(ctx, "ERROR", "No messages in list!", "31")
            bot.rotating_status = True
            bot.loop.create_task(bot.status_rotator())
            await ui_send(ctx, "ROTATOR", "Status rotation: ENABLED", "32")
        else:
            bot.rotating_status = False
            await ui_send(ctx, "ROTATOR", "Status rotation: DISABLED", "31")

    @bot.command()
    async def dot(ctx, mode: str):
        """Change your online dot color."""
        modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "inv": discord.Status.invisible}
        bot.status_dot = modes.get(mode.lower(), discord.Status.online)
        await bot.change_presence(status=bot.status_dot)
        await ui_send(ctx, "DOT", f"Set to {mode.upper()}", "34")

    @bot.command()
    async def afk(ctx, *, reason="I'm away right now."):
        bot.afk_reason = reason
        bot.afk_time = time.time() 
        await ui_send(ctx, "AFK", f"Status set: {reason}", "33")

    @bot.command()
    async def stop(ctx):
        bot.spamming = False
        bot.target_id = None
        bot.react_emoji = None
        bot.afk_reason = None
        bot.rotating_status = False
        await ui_send(ctx, "SYSTEM", "Killed all tasks.", "31")

# ─── Execution ───
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    if TOKEN:
        master_bot = Kill()
        add_commands(master_bot)
        master_bot.run(TOKEN)
