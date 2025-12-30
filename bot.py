
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import asyncio
from datetime import time as dt_time
import discord
from discord.ext import commands, tasks
from sheets import get_daily_stats, get_row_count, get_sheet_values

TOKEN = os.environ["DISCORD_TOKEN"]
STATS_CHANNEL_ID = int(os.environ["STATS_CHANNEL_ID"])
WATCH_SHEET = "Logs"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

last_known_rows = 0

# Embed builder for daily stats
def build_daily_stats_embed(rows, total):
    """
    Builds a Discord embed showing daily stats in two side-by-side columns.
    """
    embed = discord.Embed(
        title="📅 Daily Stats",
        color=discord.Color.dark_teal()
    )

    if not rows:
        embed.description = "No data available."
        return embed

    # Build table rows as a single string with columns aligned
    table_lines = ["**Person** | **Items Sent**"]
    table_lines.append("---|---")

    for person, items_sent in rows:
        table_lines.append(f"{person} | {items_sent}")

    # Join all lines into a single string
    table_content = "\n".join(table_lines)

    embed.description = f"```{table_content}```\n**Total Sent:** {total}"
    return embed


# Task: daily stats at 9AM
@tasks.loop(time=dt_time(hour=9, minute=0))
async def daily_stats_task():
    channel = bot.get_channel(STATS_CHANNEL_ID)
    if channel:
        rows, total = get_daily_stats()
        embed = build_daily_stats_embed(rows, total)
        await channel.send(embed=embed)

# Task: watch new rows in Logs
@tasks.loop(seconds=60)
async def sheet_watch_task():
    global last_known_rows
    current_rows = get_row_count(WATCH_SHEET)
    if current_rows > last_known_rows:
        new_entries = get_sheet_values(WATCH_SHEET, start_row=last_known_rows + 1)
        channel = bot.get_channel(STATS_CHANNEL_ID)
        if channel:
            for row in new_entries:
                await channel.send(f"🆕 New log entry: `{row}`")
        last_known_rows = current_rows

# On bot ready
@bot.event
async def on_ready():
    global last_known_rows
    last_known_rows = get_row_count(WATCH_SHEET)
    print(f"✅ Logged in as {bot.user}")
    daily_stats_task.start()
    sheet_watch_task.start()

bot.run(TOKEN)
