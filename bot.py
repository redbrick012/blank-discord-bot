
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951


    await interaction.response.send_message(embed=embed)

bot.tree.add_command(dailystats)

# ---------------- Tasks ---------------- #

@tasks.loop(seconds=60)  # check every minuteimport os
import discord
from discord.ext import tasks, commands
from discord import app_commands
from sheets import get_daily_stats, get_row_count, WATCH_SHEET
import asyncio
from datetime import datetime, time as dtime, timedelta

# Environment variables
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
STATS_CHANNEL_ID = int(os.environ.get("STATS_CHANNEL_ID"))

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Needed for commands
bot = commands.Bot(command_prefix="!", intents=intents)

# Keep track of last known row for the logs tab
last_known_rows = 0

# ---------------- Embed Builders ---------------- #

def build_daily_stats_embed(rows, total):
    embed = discord.Embed(
        title="📅 Daily Stats",
        color=discord.Color.dark_teal()
    )

    # Combine names and values in one line each
    stats_lines = [f"{name}: {value}" for name, value in rows]
    embed.add_field(
        name="Stats",
        value="\n".join(stats_lines) if stats_lines else "No data available.",
        inline=False
    )

    embed.add_field(
        name="Total Sent",
        value=f"**{total}**",
        inline=False
    )

    return embed

def build_new_log_embed(new_rows):
    embed = discord.Embed(
        title=f"🆕 New Log Entry in `{WATCH_SHEET}`",
        color=discord.Color.orange()
    )
    for idx, row in enumerate(new_rows, start=1):
        embed.add_field(
            name=f"Row {idx}",
            value=" | ".join(row),
            inline=False
        )
    return embed

# ---------------- Commands ---------------- #

@bot.event
async def on_ready():
    global last_known_rows
    print(f"✅ Logged in as {bot.user}")
    last_known_rows = get_row_count(WATCH_SHEET)
    # Start background tasks
    daily_stats_task.start()
    sheet_watch_task.start()

@app_commands.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await interaction.response.send_message(embed=embed)

bot.tree.add_command(dailystats)

# ---------------- Tasks ---------------- #

@tasks.loop(seconds=60)  # check every minute
async def sheet_watch_task():
    global last_known_rows
    current_rows = get_row_count(WATCH_SHEET)
    if current_rows > last_known_rows:
        new_rows = get_sheet_values(WATCH_SHEET)[last_known_rows:current_rows]
        channel = bot.get_channel(STATS_CHANNEL_ID)
        embed = build_new_log_embed(new_rows)
        await channel.send(embed=embed)
        last_known_rows = current_rows

@tasks.loop(hours=24)
async def daily_stats_task():
    now = datetime.utcnow()
    target_time = dtime(hour=9, minute=0)  # 9:00 AM UTC
    first_run = datetime.combine(now.date(), target_time)
    if now > first_run:
        first_run += timedelta(days=1)
    wait_seconds = (first_run - now).total_seconds()
    await asyncio.sleep(wait_seconds)

    channel = bot.get_channel(STATS_CHANNEL_ID)
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await channel.send(embed=embed)

# ---------------- Run Bot ---------------- #

bot.run(DISCORD_TOKEN)
