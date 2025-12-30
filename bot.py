
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import discord
from discord.ext import commands, tasks
import asyncio
import datetime
from sheets import get_daily_stats, get_row_count, get_sheet_values  # Your sheets.py helpers

# Bot configuration
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Environment variables
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
STATS_CHANNEL_ID = int(os.environ["STATS_CHANNEL_ID"])
WATCH_SHEET = os.environ.get("WATCH_SHEET", "logs")

# Track last known row for the watch sheet
last_known_rows = 0

# ------------------------
# Embed builder
# ------------------------
def build_daily_stats_embed(rows, total):
    embed = discord.Embed(
        title="📅 Daily Stats",
        color=discord.Color.dark_teal()
    )

    # Make two columns: Person | Items Sent
    value_lines = [f"{person} | {items}" for person, items in rows]
    embed.add_field(
        name="Person | Items Sent",
        value="\n".join(value_lines),
        inline=False
    )

    embed.add_field(
        name="Total Sent",
        value=f"**{total}**",
        inline=False
    )

    return embed

# ------------------------
# Commands
# ------------------------
@bot.tree.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await interaction.response.send_message(embed=embed)

# ------------------------
# Tasks
# ------------------------
@tasks.loop(time=datetime.time(hour=9, minute=0))  # runs daily at 9AM
async def daily_stats_task():
    rows, total = get_daily_stats()
    channel = bot.get_channel(STATS_CHANNEL_ID)
    embed = build_daily_stats_embed(rows, total)
    await channel.send(embed=embed)

@tasks.loop(seconds=60)  # check logs sheet every minute
async def sheet_watch_task():
    global last_known_rows
    current_rows = get_row_count(WATCH_SHEET)
    if current_rows > last_known_rows:
        channel = bot.get_channel(STATS_CHANNEL_ID)
        # Get new rows only
        new_entries = get_sheet_values(WATCH_SHEET, start_row=last_known_rows + 1, end_row=current_rows)
        message_lines = [f" | ".join(entry) for entry in new_entries]
        await channel.send(
            f"🆕 **New entries added to `{WATCH_SHEET}`**\n" + "\n".join(message_lines)
        )
        last_known_rows = current_rows

# ------------------------
# Events
# ------------------------
@bot.event
async def on_ready():
    global last_known_rows
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} (slash commands synced)")
    # Initialize last_known_rows
    last_known_rows = get_row_count(WATCH_SHEET)
    # Start tasks
    daily_stats_task.start()
    sheet_watch_task.start()

# ------------------------
# Run bot
# ------------------------
bot.run(DISCORD_TOKEN)
