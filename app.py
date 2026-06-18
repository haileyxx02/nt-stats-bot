# Required Python Modules
from discord.commands import Option
from discord.ext import commands
from fake_useragent import UserAgent
import cloudscraper
import websocket
import threading
import discord
import random
import requests
import string
import json
import time
import os
import ssl
import sys

# Discord Bot Parameters
ADMIN_ID = 1487626415863238697
bot = discord.Bot()

# Enhanced Color Scheme
class Colors:
    PRIMARY = 0x5865F2  # Discord Blurple
    SUCCESS = 0x57F287  # Green
    WARNING = 0xFEE75C  # Yellow
    ERROR = 0xED4245    # Red
    INFO = 0x5865F2     # Blue
    RACING = 0xEB459E   # Pink

# Enhanced Emojis
class Emojis:
    SUCCESS = "✅"
    ERROR = "❌"
    LOADING = "⏳"
    RACING = "🏁"
    STOP = "🛑"
    INFO = "ℹ️"
    SLOTS = "🎰"
    USER = "👤"
    STATS = "📊"
    SPEEDOMETER = "⚡"
    CHECKERED_FLAG = "🏁"
    TROPHY = "🏆"

# NitroType Bot Parameters
ua = UserAgent(platforms="desktop")
tasks = []

# Get Hashes from Bootstrap
def getVersion():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'dnt': '1',
        'priority': 'u=0, i',
        'referer': 'https://www.nitrotype.com/login',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }
    r = requests.get('https://www.nitrotype.com/garage', headers=headers).text.split('<script src="/index/')[1].split('/bootstrap.js"')[0].split('-')
    return r

VERSION_HASH, VERSION_INT = getVersion()

# NitroType Modules
def calculate_typing_time_per_letter(wpm, num_words):
    total_letters = num_words * 5
    total_seconds = (60 / wpm) * num_words
    seconds_per_letter = total_seconds / total_letters
    return seconds_per_letter

def removeBeg(text):
    return json.loads(text[1:])

def startTyping(client, words, set_wpm, min_acc):
    target_accuracy = random.uniform(min_acc, 98) / 100
    error_probability = 1 - target_accuracy
    c = 0
    e = 0
    rounds = 0
    word_s = words.replace(' ', ' \n').split('\n')
    tex_ = ''
    for word_group in word_s:
        packet_count = 0
        packet = []
        rounds += 1
        for char in word_group:
            c += 1
            if random.random() < error_probability:
                wrong_char = random.choice([ch for ch in string.ascii_letters if ch != char])
                e += 1
                client.send(
                    '5' + json.dumps(
                        {"stream": "race", "msg": "update", "payload": {"e": e, "k": [[wrong_char, random.randint(1, 500), 1, None]]}},separators=(',', ':')
                    )
                )
            packet.append([char, random.randint(1, 500), None, None])
            time.sleep(calculate_typing_time_per_letter(random.randint(set_wpm - 15, set_wpm + 15), len(words) / 5))
            total_delay = sum(p[1] for p in packet if p[1])
            if total_delay >= 450 or len(packet) >= 5:
                client.send(
                    '5' + json.dumps(
                        {"stream": "race", "msg": "update", "payload": {"t": c, "k": packet}},separators=(',', ':')
                    )
                )
                packet_count += len(packet)
                tex_ += ''.join(p[0] for p in packet)
                packet = []
            elif packet_count + len(packet) == len(word_group):
                client.send(
                    '5' + json.dumps(
                        {"stream": "race", "msg": "update", "payload": {"t": c, "k": packet}},separators=(',', ':')
                    )
                )
                packet_count += len(packet)
                tex_ += ''.join(p[0] for p in packet)
                packet = []

def nitroTypeLogin(username, password, userAgent):
    with requests.Session() as session:
        session.headers['origin'] = 'https://www.nitrotype.com'
        session.headers['referer'] = 'https://www.nitrotype.com/login'
        session.headers['user-agent'] = userAgent
        session.headers['x-username'] = username
        session.get('https://nitrotype.com/login')
        login = session.post(
            'https://www.nitrotype.com/api/v2/auth/login/username',
            json={
                'username': username,
                'password': password,
                'captchaToken': 'ignore',
                'authCode': '',
                'trustDevice': False,
                'tz': 'America/Chicago',
            }
        )
        if login.status_code == 200:
            if login.json()['status'] == 'OK':
                cookies = session.cookies
                cookies = '; '.join([cookie.name + '=' + cookie.value for cookie in cookies])
                racesPlayed = login.json().get('results', {}).get('racesPlayed')
                friends_array = []
                stickerIDS = [item['lootID'] for item in json.loads(login.text)['results']['loot'] if item['type'] == 'sticker' and item['equipped'] > 0]
                if stickerIDS == []:
                    stickerIDS = [1, 2, 3, 4, 5, 28]
                if "friends" in login.text:
                    friendsHash = login.json().get('results', {}).get('friendsHash')
                    for friend in login.json()['results'].get('friends', []):
                        friends_array.append(friend['userID'])
                else:
                    friends_array = None
                    friendsHash = None
                return login.json()['results'], userAgent, cookies, racesPlayed, friendsHash, friends_array, stickerIDS
            
            elif "No account found" in login.text or "Blocked" in login.text:
                return None, None, None, None, None, None, None
            else:
                login = session.post(
                    'https://www.nitrotype.com/api/v2/auth/login/username',
                    json = {
                        'username': username,
                        'password': password,
                        'captchaToken': "ignore",
                        'authCode': '',
                        'trustDevice': False,
                        'tz': 'America/Chicago',
                    }
                )
                if login.status_code == 200:
                    if login.json()['status'] == 'OK':
                        cookies = session.cookies
                        cookies = '; '.join([cookie.name + '=' + cookie.value for cookie in cookies])
                        racesPlayed = login.json().get('results', {}).get('racesPlayed')
                        friends_array = []
                        stickerIDS = [item['lootID'] for item in json.loads(login.text)['results']['loot'] if item['type'] == 'sticker' and item['equipped'] > 0]
                        if stickerIDS == []:
                            stickerIDS = [1, 2, 3, 4, 5, 28]
                        if "friends" in login.text:
                            friendsHash = login.json().get('results', {}).get('friendsHash')
                            for friend in login.json()['results'].get('friends', []):
                                friends_array.append(friend['userID'])
                        else:
                            friends_array = None
                            friendsHash = None
                        return login.json()['results'], userAgent, cookies, racesPlayed, friendsHash, friends_array, stickerIDS
                    else:
                        return None, None, None, None, None, None, None

def sendSticker(client, stickers):
    time.sleep(random.uniform(0, 2))
    randomSticker = int(random.choice(stickers))
    client.send(
        '5' + json.dumps({"stream":"race","msg":"chat","payload":{"chatID":randomSticker, "chatType":"sticker"}},separators=(',', ':')
        )
    )

def mainModule(auth, userAgent, discord_id, username, password, cookies, racesPlayed, friendsHash, friends_array, wpm, race_amount, min_acc, stickers):
    found = None
    for i in tasks:
        if i['discord_id'] == discord_id:
            if username.lower() not in i['tasks']:
                i['tasks'].append(username.lower())
            found = i

    if found is None:
        client_token = {
            "discord_id": discord_id,
            "tasks": [username.lower()]
        }
        tasks.append(client_token)

    headers = {
        'Upgrade': 'websocket',
        'Origin': 'https://www.nitrotype.com',
        'Connection': 'Upgrade',
        'User-Agent': userAgent,
        'Sec-WebSocket-Version': '13',
        'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
        'Cookie': cookies,
    }
    while True:
        try:
            for i in tasks:
                if i['discord_id'] == discord_id:
                    racers_ = i['tasks']
                    if racers_.count(username) == 0:
                        break

            if username.lower() not in racers_:
                break

            if race_amount <= racesPlayed:
                for task in tasks:
                    if task['discord_id'] == discord_id:
                        task['tasks'].remove(username.lower())
                return

            game_text = ''
            client = websocket.create_connection(f'wss://realtime1ws.nitrotype.com/ws?token='+auth, header=headers, sslopt={"cert_reqs": ssl.CERT_REQUIRED, "ssl_version":ssl.PROTOCOL_TLSv1_2, 'check_host':True})
            if friendsHash and friends_array is not None:
                client.send(
                    '5' + json.dumps({"stream":"notifications","type":"checkin","payload":{"path":"/race","friends":friends_array,"friendsHash":friendsHash,"racesPlayed":racesPlayed}},separators=(',', ':')
                    )
                )
            else:
                client.send(
                    '5' + json.dumps({"stream":"notifications","type":"checkin","payload":{"path":"/race","racesPlayed":racesPlayed}},separators=(',', ':')
                    )
                )
            client.send(
                '5' + json.dumps(
                    {"stream": "race", "msg": "join", "payload": {"update": f"03417", "cacheId": VERSION_HASH, "cacheIdInteger": VERSION_INT, "site": "nitrotype"}},separators=(',', ':')
                )
            )
            while True:
                try:
                    recv = client.recv()
                    if recv == '''5{"stream":"error","type":"invalid session"}''':
                        results, userAgent, cookies, racesPlayed, friendsHash, friends_array, stickers = nitroTypeLogin(username, password, userAgent)
                        if results is None:
                            for task in tasks:
                                if task['discord_id'] == discord_id:
                                    task['tasks'].remove(username.lower())
                            return
                        auth = results['token']
                        headers['Cookie'] = cookies
                        client.close()
                        break

                    if "experience" in recv:
                        racesPlayed += 1
                        client.close()
                        break

                    if recv == '1PING':
                        client.send("1PONG")
                        continue

                    if removeBeg(recv)['stream'] == 'notifications':
                        continue

                    if removeBeg(recv)['stream'] == 'auth':
                        auth = removeBeg(recv)['token']
                        continue

                    if removeBeg(recv)['msg'] == 'status':
                        if removeBeg(recv)['payload'].get('l') is not None:
                            game_text += removeBeg(recv)['payload']['l']
                        if random.randint(1,3) == 1:
                            threading.Thread(target=sendSticker, args=(client, stickers)).start()

                        if removeBeg(recv)['payload']['status'] == 'racing':
                            set_wpm = random.randint(wpm - 10, wpm + 10)
                            threading.Thread(target=startTyping, args=(client, game_text, set_wpm, min_acc,)).start()

                    if removeBeg(recv)['msg'] == 'error':
                        if removeBeg(recv)['payload']['type'] == 'captcha':
                            results, userAgent, cookies, racesPlayed, friendsHash, friends_array, stickers = nitroTypeLogin(username, password, userAgent)
                            if results is None:
                                for task in tasks:
                                    if task['discord_id'] == discord_id:
                                        task['tasks'].remove(username.lower())
                                return
                            auth = results['token']
                            headers['Cookie'] = cookies
                            client.close()
                            break

                        if removeBeg(recv)['payload']['type'] == 'in race':
                            time.sleep(3)
                            client.close()
                            break
                except:
                    client.close()
                    break
        except:
            mainModule(auth, userAgent, discord_id, username, password, cookies, racesPlayed, friendsHash, friends_array, wpm, race_amount, min_acc, stickers)
            continue

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="NitroType | Quota"))
    print("╔════════════════════════════════════╗")
    print("║   🏁     Xeno Autotyper     🏁      ║")
    print("╚════════════════════════════════════╝")
    print(f"Bot User: {bot.user.name}")
    print(f"Bot ID: {bot.user.id}")
    print("Ready to race!")

@bot.slash_command(name='racer', description="🏁 Start racing on your NitroType account")
async def racer(
    ctx, 
    username: Option(str, description="Your NitroType username"), 
    password: Option(str, description="Your NitroType password"), 
    wpm: Option(int, description="Target WPM (30-170)", min_value=30, max_value=170), 
    race_amount: Option(int, description="Number of races (0-5000)", min_value=0, max_value=5000), 
    min_accuracy: Option(int, description="Minimum accuracy % (85-94)", min_value=85, max_value=94)
):
    # Check authorization
    allowed = False
    for role in ctx.author.roles:
        if role.name in ["Buyer"]:
            allowed = True

    # Check slots
    slots = None
    for role in ctx.author.roles:
        if role.name.startswith("Slots: "):
            slots_str = role.name.replace("Slots: ", "")
            slots = int(slots_str)

    if not allowed:
        embed = discord.Embed(
            title=f"{Emojis.ERROR} Access Denied",
            description="You are not authorized to use this command.",
            color=Colors.ERROR
        )
        embed.set_footer(text="Contact an administrator for access")
        await ctx.respond(embed=embed, ephemeral=True)
        return

    if slots is None or slots <= 0:
        embed = discord.Embed(
            title=f"{Emojis.SLOTS} No Slots Available",
            description="You don't have any available slots to start racing.",
            color=Colors.WARNING
        )
        embed.set_footer(text="Purchase slots to continue racing")
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Check slot usage
    for task in tasks:
        if task['discord_id'] == ctx.author.id:
            if len(task['tasks']) >= slots:
                embed = discord.Embed(
                    title=f"{Emojis.ERROR} Slots Full",
                    description=f"You have used all **{slots}** of your available slots.",
                    color=Colors.WARNING
                )
                embed.add_field(name="Active Bots", value=f"`{len(task['tasks'])}/{slots}`", inline=False)
                embed.set_footer(text="Stop a bot to free up a slot")
                await ctx.respond(embed=embed, ephemeral=True)
                return

    # Check if already botting
    for task in tasks:
        if task['discord_id'] == ctx.author.id and username.lower() in task['tasks']:
            embed = discord.Embed(
                title=f"{Emojis.ERROR} Already Active",
                description=f"You are already botting on account **{username}**",
                color=Colors.ERROR
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

    # Login attempt
    userAgent = ua.random
    embed = discord.Embed(
        title=f"{Emojis.LOADING} Logging In",
        description=f"Attempting to login to **{username}**...",
        color=Colors.INFO
    )
    await ctx.respond(embed=embed, ephemeral=True)
    
    results, userAgent, cookies, racesPlayed, friendsHash, friends_array, stickers = nitroTypeLogin(username, password, userAgent)
    
    if results:
        embed = discord.Embed(
            title=f"{Emojis.RACING} Bot Started Successfully!",
            description=f"Quota is now racing on **{username}**",
            color=Colors.SUCCESS
        )
        embed.add_field(name=f"{Emojis.SPEEDOMETER} Target WPM", value=f"`{wpm} WPM`", inline=True)
        embed.add_field(name=f"{Emojis.CHECKERED_FLAG} Races", value=f"`{race_amount}`", inline=True)
        embed.add_field(name=f"{Emojis.TROPHY} Min Accuracy", value=f"`{min_accuracy}%`", inline=True)
        embed.set_footer(text="Good luck racing! • Use /stopracer to stop", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = discord.utils.utcnow()
        await ctx.edit(embed=embed)
        
        race_amount += racesPlayed
        threading.Thread(target=mainModule, args=(results['token'], userAgent, ctx.author.id, username, password, cookies, racesPlayed, friendsHash, friends_array, wpm, race_amount, min_accuracy, stickers)).start()
    else:
        embed = discord.Embed(
            title=f"{Emojis.ERROR} Login Failed",
            description="Your credentials are incorrect or the account is blocked.",
            color=Colors.ERROR
        )
        embed.add_field(name="Username", value=f"`{username}`", inline=False)
        embed.set_footer(text="Double check your credentials and try again")
        await ctx.edit(embed=embed)

@bot.slash_command(name='stopracer', description='🛑 Stop racing on a specific NitroType account')
async def stopracer(ctx, username: Option(str, description="NitroType username to stop")):
    for task in tasks:
        if task['discord_id'] == ctx.author.id and username.lower() in task['tasks']:
            task['tasks'].remove(username.lower())
            embed = discord.Embed(
                title=f"{Emojis.STOP} Bot Stopped",
                description=f"Successfully stopped racing for **{username}**",
                color=Colors.SUCCESS
            )
            embed.set_footer(text="Use /racer to start again", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.respond(embed=embed, ephemeral=True)
            return

    embed = discord.Embed(
        title=f"{Emojis.ERROR} Not Found",
        description=f"**{username}** is not currently being botted.",
        color=Colors.ERROR
    )
    embed.set_footer(text="Use /tasks to see active bots")
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name='stopall', description='🛑 Stop all active racing bots')
async def stopall(ctx):
    found = False
    stopped_count = 0
    
    for task in tasks:
        if task['discord_id'] == ctx.author.id:
            stopped_count = len(task['tasks'])
            task['tasks'].clear()
            found = True

    if found:
        embed = discord.Embed(
            title=f"{Emojis.STOP} All Bots Stopped",
            description=f"Successfully stopped **{stopped_count}** racing bot(s)",
            color=Colors.SUCCESS
        )
        embed.set_footer(text="All your slots are now available", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title=f"{Emojis.INFO} No Active Bots",
            description="You don't have any active racing bots to stop.",
            color=Colors.INFO
        )
        embed.set_footer(text="Use /racer to start racing")
        await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="tasks", description="📋 View all your active racing bots")
async def task(ctx):
    user_tasks = [task['tasks'] for task in tasks if ctx.author.id == task['discord_id']]
    
    if user_tasks and user_tasks[0]:
        usernames = user_tasks[0]
        embed = discord.Embed(
            title=f"{Emojis.RACING} Active Racing Bots",
            description=f"You have **{len(usernames)}** active bot(s)",
            color=Colors.PRIMARY
        )
        
        accounts_list = "\n".join([f"`{idx + 1}.` **{username}**" for idx, username in enumerate(usernames)])
        embed.add_field(name="Accounts", value=accounts_list, inline=False)
        embed.set_footer(text=f"Use /stopracer to stop a specific bot", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = discord.utils.utcnow()
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title=f"{Emojis.INFO} No Active Bots",
            description="You don't have any accounts being botted right now.",
            color=Colors.INFO
        )
        embed.set_footer(text="Use /racer to start racing")
        await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="slots", description="🎰 Check your available racing slots")
async def slots(ctx):
    slots = None
    for role in ctx.author.roles:
        if role.name.startswith("Slots: "):
            slots_str = role.name.replace("Slots: ", "")
            slots = int(slots_str)

    # Count active bots
    active_bots = 0
    for task in tasks:
        if task['discord_id'] == ctx.author.id:
            active_bots = len(task['tasks'])

    if slots is None:
        embed = discord.Embed(
            title=f"{Emojis.ERROR} No Slots Available",
            description="You don't have any racing slots assigned.",
            color=Colors.ERROR
        )
        embed.set_footer(text="Contact an administrator to get slots")
        await ctx.respond(embed=embed, ephemeral=True)
        return
    else:
        embed = discord.Embed(
            title=f"{Emojis.SLOTS} Your Racing Slots",
            description=f"**{active_bots}/{slots}** slots in use",
            color=Colors.PRIMARY
        )
        embed.add_field(name="Total Slots", value=f"`{slots}`", inline=True)
        embed.add_field(name="Active Bots", value=f"`{active_bots}`", inline=True)
        embed.add_field(name="Available", value=f"`{slots - active_bots}`", inline=True)
        
        # Progress bar
        filled = int((active_bots / slots) * 10)
        empty = 10 - filled
        progress_bar = "█" * filled + "░" * empty
        embed.add_field(name="Usage", value=f"`{progress_bar}` {int((active_bots/slots)*100)}%", inline=False)
        
        embed.set_footer(text="Use /tasks to see active bots", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.respond(embed=embed, ephemeral=True)

# ═══════════════════════════════════════════════════════════════════════
# ADMIN COMMANDS
# ═══════════════════════════════════════════════════════════════════════

@bot.slash_command(name="admintasks", description="👑 [Admin] View a user's active racing bots")
async def admintasks(ctx, discord_id: Option(str, description="Discord User ID")):
    if ctx.author.id != ADMIN_ID:
        embed = discord.Embed(
            title=f"{Emojis.ERROR} Access Denied",
            description="You are not authorized to use admin commands.",
            color=Colors.ERROR
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    discord_id = int(discord_id)
    user_tasks = [task['tasks'] for task in tasks if discord_id == task['discord_id']]

    if user_tasks and user_tasks[0]:
        usernames = user_tasks[0]
        embed = discord.Embed(
            title=f"{Emojis.STATS} User's Active Bots",
            description=f"<@{discord_id}> has **{len(usernames)}** active bot(s)",
            color=Colors.PRIMARY
        )
        
        accounts_list = "\n".join([f"`{idx + 1}.` **{username}**" for idx, username in enumerate(usernames)])
        embed.add_field(name="Accounts", value=accounts_list, inline=False)
        embed.set_footer(text="Admin View", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.timestamp = discord.utils.utcnow()
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title=f"{Emojis.INFO} No Active Bots",
            description=f"<@{discord_id}> has no active racing bots.",
            color=Colors.INFO
        )
        await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name='adminstopall', description='👑 [Admin] Stop all bots for a user')
async def adminstopall(ctx, discord_id: Option(str, description="Discord User ID")):
    if ctx.author.id != ADMIN_ID:
        embed = discord.Embed(
            title=f"{Emojis.ERROR} Access Denied",
            description="You are not authorized to use admin commands.",
            color=Colors.ERROR
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    found = False
    stopped_count = 0
    
    for task in tasks:
        if task['discord_id'] == int(discord_id):
            stopped_count = len(task['tasks'])
            task['tasks'].clear()
            found = True

    if found:
        embed = discord.Embed(
            title=f"{Emojis.STOP} Bots Stopped",
            description=f"Successfully stopped **{stopped_count}** bot(s) for <@{discord_id}>",
            color=Colors.SUCCESS
        )
        embed.set_footer(text="Admin Action", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.respond(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title=f"{Emojis.INFO} No Active Bots",
            description=f"<@{discord_id}> has no active bots to stop.",
            color=Colors.INFO
        )
        await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name='stats', description="👑 [Admin] View bot usage statistics")
async def stats(ctx):
    if ctx.author.id != ADMIN_ID:
        embed = discord.Embed(
            title=f"{Emojis.ERROR} Access Denied",
            description="You are not authorized to use admin commands.",
            color=Colors.ERROR
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    bot_stats = {}
    for task in tasks:
        user_id = task['discord_id']
        num_bots = len(task['tasks'])
        if num_bots > 0:
            bot_stats[user_id] = num_bots

    total_bots = sum(bot_stats.values())
    total_users = len(bot_stats)

    embed = discord.Embed(
        title=f"{Emojis.STATS} Bot Usage Statistics",
        description=f"**{total_bots}** total bots running across **{total_users}** user(s)",
        color=Colors.PRIMARY
    )

    if bot_stats:
        stats_text = "\n".join([f"<@{user_id}>: **{num_bots}** bot(s)" for user_id, num_bots in bot_stats.items()])
        embed.add_field(name="Active Users", value=stats_text, inline=False)
    else:
        embed.add_field(name="Active Users", value="*No active bots*", inline=False)

    embed.add_field(name="Total Bots", value=f"`{total_bots}`", inline=True)
    embed.add_field(name="Active Users", value=f"`{total_users}`", inline=True)
    embed.set_footer(text="Admin Dashboard", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed.timestamp = discord.utils.utcnow()
    
    await ctx.respond(embed=embed, ephemeral=True)

# ═══════════════════════════════════════════════════════════════════════
# START BOT
# ═══════════════════════════════════════════════════════════════════════

bot.run("MTUxNzIzNjgyNzUwMzg1MzU3OA.GK1lv6.p3wEucXKiqJZ89hCa_Fvqj0_tc6CTZqNQWnnVc")
