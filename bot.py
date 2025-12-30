
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, time, timedelta
import asyncio

from sheets import get_daily_stats, get_row_count, WATCH_SHEET, STATS_SHEET

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
    formatted_date = yesterday.strftime("%A, %d %B %Y")
    #date_str = datetime.now().strftime("%A, %d %B %Y")
    embed = discord.Embed(
        title=f"📅 Daily Stats - {formatted_date}",
        color=discord.Color.dark_teal()
    )
    if not rows:
        embed.description = "No data available."
        return embed

    people_column = "\n".join(str(name) for name, _ in rows)
    items_column = "\n".join(str(value) for _, value in rows)

    embed.add_field(name="Person", value=people_column, inline=True)
    embed.add_field(name="Items Sent", value=items_column, inline=True)
    embed.add_field(name="Total Sent", value=f"**{total}**", inline=False)
    return embed

# --- Slash command using @bot.tree.command() ---
@bot.tree.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await interaction.response.send_message(embed=embed)

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

    values = get_sheet_values(WATCH_SHEET)
    current_rows = len(values)

    if current_rows > last_known_rows:
        channel = bot.get_channel(STATS_CHANNEL_ID)
        if not channel:
            return

        # Get newly added rows
        new_rows = values[last_known_rows:current_rows]

        for row in new_rows:
            formatted = " | ".join(cell or "—" for cell in row)
            await channel.send(
                f"🆕 **New entry added to `{WATCH_SHEET}`**\n"
                f"```{formatted}```"
            )

        last_known_rows = current_rows


# --- Events ---
@bot.event
async def on_ready():
    global last_known_rows
    print(f"✅ Logged in as {bot.user}")
    # Initialize last known rows
    last_known_rows = get_row_count(WATCH_SHEET)
    # Start background tasks
    daily_stats_task.start()
    sheet_watch_task.start()
    # Sync slash commands
    await bot.tree.sync()

# --- Run bot ---
bot.run(DISCORD_TOKEN)
