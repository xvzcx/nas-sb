```python
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
bot.blacklist = set() # Store blacklisted User IDs / Channel IDs

# MDM CONFIG
MDM_DELAY = 30.0  # Strict 30-second delay as requested

@bot.event
async def on_ready():
    print(f"─── {bot.user} | Connection Established ───")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.content.startswith(bot.command_prefix): return
    uid = message.author.id

    # Autoreact Logic
    if uid in bot.targets:
        for emoji in bot.targets[uid]:
            try: await message.add_reaction(emoji.strip())
            except: continue

    # Self-logic (AFK toggle)
    if uid == bot.user.id:
        is_automated = "┎" in message.content or "**[AFK]**" in message.content or "Status: ENABLED" in message.content
        if bot.afk_reason and not is_automated:
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
    res += f"[1;{color}m{'─'*(width-2)}⚚[0m\n"
    res += "```"
    return res

# ─── STATUS & RPC ───

@bot.command()
async def rpc(ctx, mode, *, text):
    await ctx.message.delete()
    m = mode.lower()
    if m == "play": act = discord.Game(name=text)
    elif m == "listen": act = discord.Activity(type=discord.ActivityType.listening, name=text)
    elif m == "watch": act = discord.Activity(type=discord.ActivityType.watching, name=text)
    else: return
    bot.current_rpc = act
    await bot.change_presence(activity=act)
    await ctx.send(ui_box("RPC", f"{m.title()}ing: {text}", "36"), delete_after=3)

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
async def dot(ctx, mode=None):
    await ctx.message.delete()
    modes = {"online": discord.Status.online, "idle": discord.Status.idle, "dnd": discord.Status.dnd, "invisible": discord.Status.invisible}
    target = modes.get(mode.lower(), discord.Status.online) if mode else discord.Status.online
    await bot.change_presence(status=target, activity=bot.current_rpc)
    await ctx.send(ui_box("Status Dot", f"Mode: {str(target).upper()}", "32"), delete_after=3)

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

# ─── SOCIAL ENGINE ───

@bot.command()
async def autoreact(ctx, user: discord.User, *, emojis):
    await ctx.message.delete()
    bot.targets[user.id] = emojis.split()
    await ctx.send(ui_box("Autoreact", f"Target: {user.name}\nEmojis: {emojis}", "34"), delete_after=5)

@bot.command()
async def stopreact(ctx, user: discord.User = None):
    await ctx.message.delete()
    if user is None: bot.targets = {}
    elif user.id in bot.targets: bot.targets.pop(user.id)
    await ctx.send(ui_box("Autoreact", "Tracking Stopped", "31"), delete_after=3)

@bot.command()
async def targets(ctx):
    await ctx.message.delete()
    if not bot.targets: return await ctx.send(ui_box("Targets", "No active targets", "34"), delete_after=5)
    body = "\n".join([f"» {bot.get_user(u)}: {' '.join(e)}" for u, e in bot.targets.items()])
    await ctx.send(ui_box("Target List", body, "34"), delete_after=10)

@bot.command()
async def mock(ctx, user: discord.Member = None):
    await ctx.message.delete()
    bot.mock_target = user.id if user else None
    state = f"Targeting: {user.name}" if user else "Disabled"
    await ctx.send(ui_box("Mock", state, "31"), delete_after=5)

@bot.command()
async def uwu(ctx, user: discord.Member = None):
    await ctx.message.delete()
    bot.uwu_target = user.id if user else None
    state = f"Targeting: {user.name}" if user else "Disabled"
    await ctx.send(ui_box("Uwu", state, "35"), delete_after=5)

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

# ─── UTILITY ENGINE ───

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
                await asyncio.sleep(0.005)
            except: continue

@bot.command()
async def spam(ctx, n: int, *, text):
    await ctx.message.delete()
    bot.spamming = True
    for _ in range(n):
        if not bot.spamming: break
        try:
            await ctx.send(text)
            await asyncio.sleep(0.2)
        except: await asyncio.sleep(1)

@bot.command()
async def blacklist(ctx, uid: str = None):
    """View MDM blacklist log or add/remove a user ID from skipping"""
    await ctx.message.delete()
    if uid is None:
        if not bot.blacklist:
            return await ctx.send(ui_box("Blacklist", "No blacklisted targets", "31"), delete_after=5)
        
        # Resolve user display names safely
        resolved_names = []
        for b_id in bot.blacklist:
            user = bot.get_user(b_id)
            if not user:
                try:
                    user = await bot.fetch_user(b_id)
                except:
                    user = None
            name = user.name if user else f"Unknown ({b_id})"
            resolved_names.append(f"» {name}")
            
        return await ctx.send(ui_box("Blacklist Log", "\n".join(resolved_names), "31"), delete_after=15)

    try:
        target_id = int(uid)
    except ValueError:
        return await ctx.send(ui_box("Error", "Invalid UID format", "31"), delete_after=5)

    if target_id in bot.blacklist:
        bot.blacklist.remove(target_id)
        await ctx.send(ui_box("Blacklist", f"Removed ID:\n{target_id}", "32"), delete_after=5)
    else:
        bot.blacklist.add(target_id)
        await ctx.send(ui_box("Blacklist", f"Added ID:\n{target_id}", "31"), delete_after=5)

@bot.command()
async def mdm(ctx, choice: str = None, *, message: str = None):
    """Launches an interactive setup menu OR processes direct mass DMs immediately"""
    await ctx.message.delete()
    
    # ─── PATH A: DIRECT EXECUTION (Instant, bypasses menus entirely) ───
    if choice in ["1", "2", "3"] and message is not None:
        dm_text = message
        targets_dict = {}
        
        # Gather Target Data
        server_members = []
        if choice == "1":
            for g in bot.guilds:
                for member in g.members:
                    if not member.bot and member.id != bot.user.id:
                        server_members.append(member)
            friends_list = bot.friends if hasattr(bot, 'friends') else (bot.user.friends if hasattr(bot.user, 'friends') else [])
            for friend in friends_list:
                if not friend.bot:
                    targets_dict[friend.id] = friend

        if choice == "1": # All
            for m in server_members:
                targets_dict[m.id] = m
            for c in bot.private_channels:
                if isinstance(c, discord.DMChannel) and c.recipient:
                    if not c.recipient.bot and c.recipient.id != bot.user.id:
                        targets_dict[c.recipient.id] = c.recipient
                elif isinstance(c, discord.GroupChannel):
                    targets_dict[c.id] = c
                    
        elif choice == "2": # Open DMs
            for c in bot.private_channels:
                if isinstance(c, discord.DMChannel) and c.recipient:
                    if not c.recipient.bot and c.recipient.id != bot.user.id:
                        targets_dict[c.recipient.id] = c.recipient
                        
        elif choice == "3": # Group Chats
            for c in bot.private_channels:
                if isinstance(c, discord.GroupChannel):
                    targets_dict[c.id] = c
            
        # Blacklist Filtering
        targets = []
        blacklisted_count = 0
        for t_id, target in targets_dict.items():
            if t_id in bot.blacklist:
                blacklisted_count += 1
                continue
            targets.append(target)
            
        if not targets:
            return await ctx.send(ui_box("MDM Status", f"No targets found.\n[1;30mSkipped {blacklisted_count} blacklisted.[0m", "31"), delete_after=5)
            
        random.shuffle(targets)
        total_targets = len(targets)
        status_msg = await ctx.send(ui_box("MDM Initialized", f"Dispatching: {total_targets} targets\nBlacklist Skipped: {blacklisted_count}\nDelay: 30s", "32"))
        
        # Dispatch Phase
        sent, failed = 0, 0
        for index, member in enumerate(targets):
            current_count = index + 1
            try:
                if isinstance(member, discord.GroupChannel):
                    personalized = dm_text.replace("<ping>", "").replace("<user>", member.name or "Group Chat")
                else:
                    personalized = dm_text.replace("<ping>", member.mention).replace("<user>", member.display_name if hasattr(member, 'display_name') else member.name)
                
                await member.send(personalized)
                sent += 1
            except:
                failed += 1
                
            progress_body = (
                f"Progress: ({current_count}/{total_targets})\n"
                f"Success: {sent}\n"
                f"Failed: {failed}\n"
                f"Blacklisted: {blacklisted_count}"
            )
            await status_msg.edit(content=ui_box("MDM Active", progress_body, "32"))
                
            if index < len(targets) - 1:
                await asyncio.sleep(MDM_DELAY)
            
        final_body = (
            f"Total Processed: ({total_targets}/{total_targets})\n"
            f"Success: {sent}\n"
            f"Failed: {failed}\n"
            f"Blacklist Skipped: {blacklisted_count}"
        )
        return await status_msg.edit(content=ui_box("MDM Complete", final_body, "32"), delete_after=15)

    # ─── PATH B: INTERACTIVE CONFIG MENU (Zero timeouts fallback) ───
    menu_body = (
        "[1;32m[1][0m ┃ All Targets (Server/DM/Group)\n"
        "[1;34m[2][0m ┃ Open DMs Only\n"
        "[1;35m[3][0m ┃ Group Chats Only\n"
        "[1;31m[4][0m ┃ Cancel Setup"
    )
    menu_msg = await ctx.send(ui_box("MDM Target Setup", menu_body, "36"))
    
    def check(m):
        return m.channel.id == ctx.channel.id and m.author.id == ctx.author.id

    try:
        choice_msg = await bot.wait_for('message', check=check, timeout=None)
        interactive_choice = choice_msg.content.strip()
        await choice_msg.delete()
        
        if interactive_choice == "4" or interactive_choice.lower() == "cancel":
            return await menu_msg.edit(content=ui_box("MDM Status", "Process Cancelled.", "31"), delete_after=5)
            
        if interactive_choice not in ["1", "2", "3"]:
            return await menu_msg.edit(content=ui_box("MDM Status", "Invalid Selection.", "31"), delete_after=5)
        
        await menu_msg.edit(content=ui_box("MDM Input Msg", "Type your message below:\n[1;30m(Supports <user> / <ping>)[0m", "35"))
        
        content_msg = await bot.wait_for('message', check=check, timeout=None)
        dm_text = content_msg.content
        await content_msg.delete()
        
        # Filter and compile targets
        targets_dict = {}
        server_members = []
        if interactive_choice == "1":
            for g in bot.guilds:
                for member in g.members:
                    if not member.bot and member.id != bot.user.id:
                        server_members.append(member)
            friends_list = bot.friends if hasattr(bot, 'friends') else (bot.user.friends if hasattr(bot.user, 'friends') else [])
            for friend in friends_list:
                if not friend.bot:
                    targets_dict[friend.id] = friend

        if interactive_choice == "1":
            for m in server_members:
                targets_dict[m.id] = m
            for c in bot.private_channels:
                if isinstance(c, discord.DMChannel) and c.recipient:
                    if not c.recipient.bot and c.recipient.id != bot.user.id:
                        targets_dict[c.recipient.id] = c.recipient
                elif isinstance(c, discord.GroupChannel):
                    targets_dict[c.id] = c
        elif interactive_choice == "2":
            for c in bot.private_channels:
                if isinstance(c, discord.DMChannel) and c.recipient:
                    if not c.recipient.bot and c.recipient.id != bot.user.id:
                        targets_dict[c.recipient.id] = c.recipient
        elif interactive_choice == "3":
            for c in bot.private_channels:
                if isinstance(c, discord.GroupChannel):
                    targets_dict[c.id] = c
            
        targets = []
        blacklisted_count = 0
        for t_id, target in targets_dict.items():
            if t_id in bot.blacklist:
                blacklisted_count += 1
                continue
            targets.append(target)
            
        if not targets:
            return await menu_msg.edit(content=ui_box("MDM Status", f"No targets found.\n[1;30mSkipped {blacklisted_count} blacklisted.[0m", "31"), delete_after=5)
            
        random.shuffle(targets)
        total_targets = len(targets)
        await menu_msg.edit(content=ui_box("MDM Initialized", f"Dispatching: {total_targets} targets\nBlacklist Skipped: {blacklisted_count}\nDelay: 30s", "32"))
        
        # Dispatch Phase
        sent, failed = 0, 0
        for index, member in enumerate(targets):
            current_count = index + 1
            try:
                if isinstance(member, discord.GroupChannel):
                    personalized = dm_text.replace("<ping>", "").replace("<user>", member.name or "Group Chat")
                else:
                    personalized = dm_text.replace("<ping>", member.mention).replace("<user>", member.display_name if hasattr(member, 'display_name') else member.name)
                
                await member.send(personalized)
                sent += 1
            except:
                failed += 1
                
            progress_body = (
                f"Progress: ({current_count}/{total_targets})\n"
                f"Success: {sent}\n"
                f"Failed: {failed}\n"
                f"Blacklisted: {blacklisted_count}"
            )
            await menu_msg.edit(content=ui_box("MDM Active", progress_body, "32"))
                
            if index < len(targets) - 1:
                await asyncio.sleep(MDM_DELAY)
            
        final_body = (
            f"Total Processed: ({total_targets}/{total_targets})\n"
            f"Success: {sent}\n"
            f"Failed: {failed}\n"
            f"Blacklist Skipped: {blacklisted_count}"
        )
        await menu_msg.edit(content=ui_box("MDM Complete", final_body, "32"), delete_after=15)
        
    except Exception as e:
        await menu_msg.edit(content=ui_box("MDM Error", f"An error occurred:\n{str(e)[:40]}", "31"), delete_after=5)

@bot.command()
async def ping(ctx):
    await ctx.message.delete()
    ms = round(bot.latency * 1000)
    await ctx.send(ui_box("Latency", f"Ping: {ms}ms", "32"), delete_after=5)

@bot.command()
async def stop(ctx):
    await ctx.message.delete()
    bot.spamming = False
    bot.targets = {}; bot.mock_target = bot.uwu_target = bot.afk_reason = None
    await ctx.send(ui_box("Halt", "All tasks killed.", "31"), delete_after=3)

# ─── HELP ENGINE ───

@bot.command()
async def help(ctx, cat=None):
    await ctx.message.delete()
    if not cat:
        body = "[1;32m» Status[0m\n[1;34m» Social[0m\n[1;35m» Fun[0m\n[1;31m» Utility[0m"
        return await ctx.send(ui_box("Main Menu", body, "37"), delete_after=15)
    
    c = cat.lower()
    if c == "status":
        body = "[1;32m» rpc [m] [t][0m\n[1;32m» customrpc [id] [img] [t] [d][0m\n[1;32m» streaming [t] [d][0m\n[1;32m» afk [reason][0m\n[1;32m» afklog[0m\n[1;32m» dot [mode][0m\n[1;32m» clearstatus[0m"
        color = "32"
    elif c == "social":
        body = "[1;34m» autoreact [@u] [e][0m\n[1;34m» stopreact [@u][0m\n[1;34m» targets[0m\n[1;34m» mock [@u][0m\n[1;34m» uwu [@u][0m"
        color = "34"
    elif c == "fun":
        body = "[1;35m» dicksize [@u][0m\n[1;35m» gaymeter [@u][0m"
        color = "35"
    elif c == "utility":
        body = "[1;31m» purge [n][0m\n[1;31m» spam [n] [t][0m\n[1;31m» mdm[0m\n[1;31m» blacklist [uid][0m\n[1;31m» ping[0m\n[1;31m» stop[0m"
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

```
