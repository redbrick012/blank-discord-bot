
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, time, timedelta
import asyncio

from sheets import get_daily_stats, get_row_count, get_sheet_values, WATCH_SHEET, STATS_SHEET

# --- Environment Variables ---
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
STATS_CHANNEL_ID = int(os.environ["STATS_CHANNEL_ID"])

# --- Discord Setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)  # Use commands.Bot for discord.py

# --- Track last known rows for logs sheet ---
last_known_rows = 0

# --- Embed builder ---
def build_daily_stats_embed(rows, total):
    yesterday = datetime.now() - timedelta(days=1)

    # Function to convert header text to bold-looking Unicode
    def bold_text(text):
        bold_map = str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
            "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘷𝘄𝘅𝘆𝘇"
        )
        return text.translate(bold_map)

    # Prepare table
    lines = []
    lines.append("```")
    lines.append(f"{bold_text('Person'):<15} | {bold_text('Items Sent'):>10}")
    lines.append("═" * 28)

    for person, count in rows:
        lines.append(f"{person:<15} | {count:>10}")

    lines.append("═" * 28)
    lines.append(f"💰 {bold_text('Total Sent'):<13} | {total:>10}")
    lines.append("```")

    table = "\n".join(lines)

    embed = discord.Embed(
        title=f"📅 Daily Stats – {yesterday.strftime('%A, %d %B %Y')}",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Daily Breakdown",
        value=table,
        inline=False
    )

    return embed

# --- Slash command using @bot.tree.command() ---
@bot.tree.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):

    await interaction.response.defer()  # ✅ THIS LINE FIXES 10015

    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)

    await interaction.followup.send(embed=embed)


# --- Daily stats task at 9 AM ---
@tasks.loop(time=time(hour=9, minute=0, second=0))
async def daily_stats_task():
    channel = bot.get_channel(STATS_CHANNEL_ID)
    if not channel:
        print("Stats channel not found.")
        return
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await channel.send(embed=embed)

# --- Sheet watcher task ---
@tasks.loop(seconds=60)
async def sheet_watch_task():
    global last_known_rows
    
    print("🔍 sheet_watch_task tick (loop running)")
   
    values = get_sheet_values(WATCH_SHEET)
    current_rows = len(values)

    # Nothing new
    if current_rows <= last_known_rows:
        return

    channel = bot.get_channel(STATS_CHANNEL_ID)
    if not channel:
        return

    # Get ONLY newly appended rows
    new_rows = values[last_known_rows:current_rows]

    for row in new_rows:
        formatted = " | ".join(cell if cell else "—" for cell in row)

        await channel.send(
            f"🆕 **New entry added to `{WATCH_SHEET}`**\n"
            f"```text\n{formatted}\n```"
        )

    last_known_rows = current_rows
# --- Events ---
@bot.event
async def on_ready():
    global last_known_rows

    print(f"✅ Logged in as {bot.user}")

    # Initialize last known rows
    last_known_rows = get_row_count(WATCH_SHEET)

    # Start background tasks safely
    if not daily_stats_task.is_running():
        daily_stats_task.start()

    if not sheet_watch_task.is_running():
        sheet_watch_task.start()

    # Sync slash commands
    await bot.tree.sync()

# --- Run bot ---
bot.run(DISCORD_TOKEN)
