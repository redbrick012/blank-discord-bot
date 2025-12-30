
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import asyncio
import discord
from discord.ext import tasks
from sheets import get_daily_stats, get_row_count, get_sheet_values, WATCH_SHEET, STATS_SHEET

# --------------------
# Environment variables
# --------------------
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
STATS_CHANNEL_ID = int(os.environ["STATS_CHANNEL_ID"])

# --------------------
# Bot setup
# --------------------
intents = discord.Intents.default()
bot = discord.Bot(intents=intents)  # Using discord.Bot for app commands

# --------------------
# Embed builder
# --------------------
def build_daily_stats_embed(rows, total):
    embed = discord.Embed(
        title="📅 Daily Stats",
        color=discord.Color.dark_teal()
    )

    # Display rows side by side in columns
    people = []
    items = []
    for name, count in rows:
        people.append(name)
        items.append(str(count))

    embed.add_field(name="Person", value="\n".join(people), inline=True)
    embed.add_field(name="Items Sent", value="\n".join(items), inline=True)
    embed.add_field(name="Total Sent", value=f"**{total}**", inline=False)

    return embed

# --------------------
# Slash command
# --------------------
@bot.tree.command(name="dailystats", description="Shows daily stats from the sheet")
async def dailystats(interaction: discord.Interaction):
    rows, total = get_daily_stats()
    if not rows:
        await interaction.response.send_message("📅 Daily Stats\nNo data available.")
        return

    embed = build_daily_stats_embed(rows, total)
    await interaction.response.send_message(embed=embed)

# --------------------
# Sheet watch task
# --------------------
last_known_rows = 0

@tasks.loop(seconds=60)  # check every minute
async def sheet_watch_task():
    global last_known_rows
    try:
        current_rows = get_row_count(WATCH_SHEET)
        if current_rows > last_known_rows:
            channel = bot.get_channel(STATS_CHANNEL_ID)
            new_values = get_sheet_values(WATCH_SHEET, f"A{last_known_rows+1}:Z{current_rows}")
            message = f"🆕 **New entry added to `{WATCH_SHEET}`**\n"
            for row in new_values:
                message += " | ".join(row) + "\n"
            await channel.send(message)
            last_known_rows = current_rows
    except Exception as e:
        print("Error in sheet_watch_task:", e)

# --------------------
# On ready event
# --------------------
@bot.event
async def on_ready():
    global last_known_rows
    await bot.tree.sync()  # ensures slash commands are registered
    last_known_rows = get_row_count(WATCH_SHEET)
    sheet_watch_task.start()
    print(f"Logged in as {bot.user} and tasks started.")

# --------------------
# Run the bot
# --------------------
bot.run(DISCORD_TOKEN)

