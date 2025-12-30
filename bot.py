
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import asyncio
import discord
from discord.ext import commands, tasks, datetime
from sheets import get_daily_stats, get_row_count, get_sheet_values

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
STATS_CHANNEL_ID = int(os.environ["STATS_CHANNEL_ID"])
LOGS_CHANNEL_ID = int(os.environ["LOGS_CHANNEL_ID"])
WATCH_SHEET = "logs"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

last_known_rows = 0

# -------------------------
# Daily Stats Embed
# -------------------------
def build_daily_stats_embed(rows):
    total = sum(value for _, value in rows)
    embed = discord.Embed(title="📅 Daily Stats", color=discord.Color.dark_teal())

    embed.add_field(
        name="Person",
        value="\n".join(name for name, _ in rows),
        inline=True
    )
    embed.add_field(
        name="Items Sent",
        value="\n".join(str(value) for _, value in rows),
        inline=True
    )
    embed.add_field(name="Total Sent", value=f"**{total}**", inline=False)
    return embed

# -------------------------
# Commands
# -------------------------
@bot.tree.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):
    rows = get_daily_stats()
    if not rows:
        await interaction.response.send_message("No data found.")
        return

    embed = build_daily_stats_embed(rows)
    await interaction.response.send_message(embed=embed)

# -------------------------
# Background Tasks
# -------------------------
@tasks.loop(time=datetime.time(hour=9, minute=0, second=0))
async def daily_stats_task():
    try:
        rows = get_daily_stats()
        if not rows:
            return
        embed = build_daily_stats_embed(rows)
        channel = bot.get_channel(STATS_CHANNEL_ID)
        await channel.send(embed=embed)
    except Exception as e:
        print("Error in daily_stats_task:", e)

async def sheet_watch_task():
    global last_known_rows
    await bot.wait_until_ready()
    channel = bot.get_channel(LOGS_CHANNEL_ID)
    last_known_rows = get_row_count(WATCH_SHEET)

    while not bot.is_closed():
        try:
            current_rows = get_row_count(WATCH_SHEET)
            if current_rows > last_known_rows:
                all_values = get_sheet_values(os.environ["SHEET_ID"], WATCH_SHEET)
                new_rows = all_values[last_known_rows:current_rows]

                for row in new_rows:
                    row_text = " | ".join(str(cell) for cell in row)
                    await channel.send(f"🆕 **New entry added to `{WATCH_SHEET}`**\n`{row_text}`")

                last_known_rows = current_rows

            await asyncio.sleep(60)  # check every minute
        except Exception as e:
            print("Error in sheet_watch_task:", e)
            await asyncio.sleep(60)

# -------------------------
# Events
# -------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} (slash commands synced)")

# -------------------------
# Start Background Tasks
# -------------------------
bot.loop.create_task(sheet_watch_task())
daily_stats_task.start()  # run daily stats loop

bot.run(DISCORD_TOKEN)
