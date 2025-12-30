
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import asyncio
import discord
from discord.ext import commands, tasks
from sheets import get_daily_stats, get_row_count, get_sheet_values, WATCH_SHEET, STATS_SHEET

# --------------------
# Discord Setup
# --------------------
intents = discord.Intents.default()
intents.message_content = True  # only needed if reading messages

bot = commands.Bot(
    command_prefix="!",  # needed for commands.Bot but slash commands use bot.tree
    intents=intents,
    help_command=None
)

STATS_CHANNEL_ID = int(os.environ["STATS_CHANNEL_ID"])

# --------------------
# Embed Builder
# --------------------
def build_daily_stats_embed(rows, total):
    embed = discord.Embed(
        title=f"📅 Daily Stats - {datetime.utcnow():%A, %d %B %Y}",
        color=discord.Color.dark_teal()
    )

    # Two-column layout
    name_value = "\n".join(name for name, _ in rows)
    items_value = "\n".join(str(value) for _, value in rows)

    embed.add_field(name="Person", value=name_value, inline=True)
    embed.add_field(name="Items Sent", value=items_value, inline=True)
    embed.add_field(name="Total Sent", value=f"**{total}**", inline=False)

    return embed

# --------------------
# Slash Command
# --------------------
@bot.tree.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):
    rows, total = get_daily_stats()
    if not rows:
        await interaction.response.send_message("📅 Daily Stats\nNo data available.")
        return

    embed = build_daily_stats_embed(rows, total)
    await interaction.response.send_message(embed=embed)

# --------------------
# Sheet Watcher
# --------------------
last_known_rows = 0  # will be updated on_ready

@tasks.loop(seconds=60)
async def sheet_watch_task():
    global last_known_rows
    current_rows = get_row_count(WATCH_SHEET)

    if current_rows > last_known_rows:
        channel = bot.get_channel(STATS_CHANNEL_ID)
        # Fetch new rows
        all_values = get_sheet_values(WATCH_SHEET)
        new_rows = all_values[last_known_rows:current_rows]  # new entries
        msg = "🆕 **New row(s) added:**\n"
        for row in new_rows:
            msg += " | ".join(row) + "\n"
        await channel.send(msg)
        last_known_rows = current_rows

# --------------------
# Background Tasks
# --------------------
@tasks.loop(time=time(hour=9, minute=0))  # Runs daily at 9:00 AM
async def daily_stats_task():
    try:
        rows, total = get_daily_stats()  # your function to fetch data from the sheet
        embed = build_daily_stats_embed(rows, total)
        channel = bot.get_channel(STATS_CHANNEL_ID)
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Error in daily_stats_task: {e}")

# --------------------
# Events
# --------------------
@bot.event
async def on_ready():
    global last_known_rows
    print(f"✅ Logged in as {bot.user}")
    last_known_rows = get_row_count(WATCH_SHEET)

    # Start background tasks
    daily_stats_task.start()
    sheet_watch_task.start()

    # Sync slash commands
    await bot.tree.sync()
    print("✅ Slash commands synced.")

# --------------------
# Run Bot
# --------------------
bot.run(os.environ["DISCORD_TOKEN"])
