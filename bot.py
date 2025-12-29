
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, time as dt_time

from sheets import get_sheet_data

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
WORKSHEET_NAME = "Daily Stats"
DAILY_RANGE = "B4:C12"

CHANNEL_ID = 1455146969579126951  # Discord channel for daily posts

CACHE_TTL_SECONDS = 300  # 5 minutes

# -------------------------------------------------
# BOT SETUP
# -------------------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------------------------------
# SHEET CACHE
# -------------------------------------------------
cached_data = None
last_cache_time = None

def get_cached_sheet():
    global cached_data, last_cache_time

    now = datetime.utcnow()

    if cached_data and last_cache_time:
        age = (now - last_cache_time).total_seconds()
        if age < CACHE_TTL_SECONDS:
            return cached_data

    data = get_sheet_data(
        SPREADSHEET_ID,
        WORKSHEET_NAME,
        DAILY_RANGE
    )

    if data:
        cached_data = data
        last_cache_time = now

    return data

# -------------------------------------------------
# TABLE FORMATTER
# -------------------------------------------------
def format_table(data):
    if not data or not any(data):
        return "No data."

    # Convert list of dicts to list of lists
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [headers]
        for item in data:
            rows.append([str(item.get(h, "")) for h in headers])
    else:
        # Ensure all rows are lists and have same length
        max_len = max(len(row) for row in data)
        rows = [ [str(cell) for cell in row] + [""]*(max_len - len(row)) for row in data ]

    # Calculate column widths safely
    col_widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]

    # Build formatted table
    formatted_rows = []
    for row in rows:
        line = " | ".join(row[i].ljust(col_widths[i]) for i in range(len(row)))
        formatted_rows.append(line)

    return "\n".join(formatted_rows)

# -------------------------------------------------
# SLASH COMMANDS
# -------------------------------------------------
@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.tree.command(
    name="dailystats",
    description="Show Daily Stats (B4:C12)"
)
async def dailystats(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    data = get_cached_sheet()

    if not data:
        await interaction.followup.send("❌ No data found.")
        return

    table = format_table(data)
    await interaction.followup.send(
        f"📊 **Daily Stats**\n```{table}```"
    )

# -------------------------------------------------
# DAILY 9 AM UTC POST
# -------------------------------------------------
last_post_date = None

@tasks.loop(minutes=1)
async def daily_post():
    global last_post_date

    now = datetime.utcnow()
    today = now.date()

    if now.hour == 9 and now.minute == 0:
        if last_post_date == today:
            return

        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Daily post channel not found")
            return

        data = get_cached_sheet()
        if not data:
            await channel.send("❌ No Daily Stats available.")
            return

        table = format_table(data)
        await channel.send(
            f"📅 **Daily Stats**\n```{table}```"
        )

        last_post_date = today

# -------------------------------------------------
# EVENTS
# -------------------------------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

    if not daily_post.is_running():
        daily_post.start()

# -------------------------------------------------
# RUN
# -------------------------------------------------
bot.run(DISCORD_TOKEN)
